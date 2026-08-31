import math
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from app.config import settings


class RecognitionService:
    """Real face detection + ArcFace embedding service.

    InsightFace's FaceAnalysis combines face detection (SCRFD) and face
    recognition (ArcFace). The model is loaded once and reused.
    """

    _face_app = None

    @classmethod
    def _get_face_app(cls):
        if cls._face_app is None:
            try:
                import insightface
            except ImportError as exc:
                raise RuntimeError(
                    "InsightFace is not installed. Install backend requirements "
                    "and run the app again."
                ) from exc

            provider = settings.INSIGHTFACE_PROVIDER.upper()
            if provider == "CUDA":
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            else:
                providers = ["CPUExecutionProvider"]

            cls._face_app = insightface.app.FaceAnalysis(
                name=settings.INSIGHTFACE_MODEL,
                providers=providers,
            )
            # 640 gives better recall for smaller/back-row faces.
            cls._face_app.prepare(
                ctx_id=0 if provider == "CUDA" else -1,
                det_size=(640, 640),
            )
        return cls._face_app

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        a = np.asarray(v1, dtype=np.float32)
        b = np.asarray(v2, dtype=np.float32)
        na = float(np.linalg.norm(a))
        nb = float(np.linalg.norm(b))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    @classmethod
    def generate_face_embedding(
        cls,
        image_path: Path,
        seed_text: Optional[str] = None,
    ) -> List[float]:
        """Generate a real normalized ArcFace embedding from an image.

        The image should contain one enrolled face. If multiple faces are
        present, the largest/highest-confidence face is selected.
        """
        import cv2

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        faces = cls._get_face_app().get(image)
        if not faces:
            raise ValueError("No face detected in enrollment image.")

        face = max(
            faces,
            key=lambda f: (
                float((f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1])),
                float(getattr(f, "det_score", 0.0)),
            ),
        )
        embedding = getattr(face, "normed_embedding", None)
        if embedding is None:
            embedding = getattr(face, "embedding", None)
        if embedding is None:
            raise ValueError("Face recognition model did not return an embedding.")

        vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
        if vector.size != 512:
            raise ValueError(f"Expected 512-dim ArcFace embedding, got {vector.size}.")
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            raise ValueError("Invalid zero-length face embedding.")
        return (vector / norm).astype(np.float32).tolist()

    @classmethod
    def detect_faces_in_photo(
        cls,
        photo_path: Path,
        photo_order: int = 1,
    ) -> List[Dict[str, Any]]:
        """Detect every usable face in a classroom image and extract embeddings."""
        import cv2

        image = cv2.imread(str(photo_path))
        if image is None:
            raise ValueError(f"Could not read image: {photo_path}")

        faces = cls._get_face_app().get(image)
        detected_faces: List[Dict[str, Any]] = []

        for index, face in enumerate(faces, start=1):
            bbox = np.asarray(face.bbox).astype(int).tolist()
            x1, y1, x2, y2 = bbox
            w = max(0, x2 - x1)
            h = max(0, y2 - y1)

            embedding = getattr(face, "normed_embedding", None)
            if embedding is None:
                embedding = getattr(face, "embedding", None)
            if embedding is None:
                continue

            vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
            if vector.size != 512:
                continue
            norm = float(np.linalg.norm(vector))
            if norm == 0:
                continue

            det_score = float(getattr(face, "det_score", 0.0))
            # Quality is intentionally conservative: detection confidence plus
            # face size. A tiny/back-row face can remain detectable but is less
            # likely to be promoted to a confident attendance match.
            image_h, image_w = image.shape[:2]
            area_ratio = (w * h) / max(1, image_w * image_h)
            size_score = min(1.0, math.sqrt(area_ratio) * 12.0)
            quality = max(0.0, min(1.0, 0.7 * det_score + 0.3 * size_score))

            detected_faces.append({
                "face_index": index,
                "bounding_box": {
                    "x": x1,
                    "y": y1,
                    "w": w,
                    "h": h,
                },
                "quality_score": round(quality, 4),
                "embedding": (vector / norm).astype(np.float32).tolist(),
            })

        return detected_faces

    @classmethod
    def match_faces_against_class_roster(
        cls,
        detected_faces: List[Dict[str, Any]],
        enrolled_students: List[Dict[str, Any]],
        photo_order: int = 1,
    ) -> Dict[str, Any]:
        """Match each detected face only against the selected class roster."""
        confident_matches = []
        review_matches = []
        unknown_faces = []
        matched_student_ids = set()

        for face in detected_faces:
            face_emb = face["embedding"]
            best_student = None
            best_score = -1.0

            for student in enrolled_students:
                student_emb = student.get("embedding")
                if not student_emb:
                    continue
                score = cls.cosine_similarity(face_emb, student_emb)
                if score > best_score:
                    best_score = score
                    best_student = student

            face_label = f"Face #{face['face_index']}"
            quality = float(face.get("quality_score", 0.0))

            # A face must satisfy both identity similarity and minimum image
            # quality before being automatically marked present.
            confident_threshold = settings.SIMILARITY_THRESHOLD_CONFIDENT
            review_threshold = settings.SIMILARITY_THRESHOLD_REVIEW

            if (
                best_student
                and best_score >= confident_threshold
                and quality >= settings.MIN_FACE_QUALITY
            ):
                if best_student["id"] not in matched_student_ids:
                    confident_matches.append({
                        "face_id": face_label,
                        "student_id": best_student["id"],
                        "name": best_student["name"],
                        "student_number": best_student["student_number"],
                        "confidence_score": round(best_score, 4),
                        "confidence": f"{int(best_score * 100)}%",
                        "source_photo_order": photo_order,
                    })
                    matched_student_ids.add(best_student["id"])
                else:
                    review_matches.append({
                        "face_id": face_label,
                        "candidate_student_id": best_student["id"],
                        "candidate_name": best_student["name"],
                        "confidence_score": round(best_score, 4),
                        "confidence": f"{int(best_score * 100)}%",
                        "source_photo_order": photo_order,
                    })
            elif best_student and best_score >= review_threshold:
                review_matches.append({
                    "face_id": face_label,
                    "candidate_student_id": best_student["id"],
                    "candidate_name": best_student["name"],
                    "confidence_score": round(best_score, 4),
                    "confidence": f"{int(best_score * 100)}%",
                    "source_photo_order": photo_order,
                })
            else:
                unknown_faces.append({
                    "face_id": face_label,
                    "candidate": "Unknown",
                    "source_photo_order": photo_order,
                })

        not_detected = [
            {
                "student_id": student["id"],
                "name": student["name"],
                "student_number": student["student_number"],
                "status": "Not detected",
            }
            for student in enrolled_students
            if student["id"] not in matched_student_ids
        ]

        return {
            "confident": confident_matches,
            "review": review_matches,
            "unknown": unknown_faces,
            "not_detected": not_detected,
        }


recognition_service = RecognitionService()
