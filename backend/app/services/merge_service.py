from typing import List, Dict, Any, Set
from app.models.attendance import RecognitionStatus

class MergeService:
    @staticmethod
    def merge_photo_recognition_results(
        photo1_results: Dict[str, Any],
        photo2_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merges recognition results from Photo 1 and Photo 2 deterministically:
        - Confident matches from Photo 1 are preserved.
        - Confident matches from Photo 2 promote previously Uncertain/Not Detected students.
        - Duplicate student recognitions are deduplicated to the highest confidence.
        - Remaining uncertain and unknown faces from both photos are aggregated for review.
        - Not detected list is updated to reflect only students still unmatched across all photos.
        """
        # Map of student_id -> best confident match info
        confident_by_student: Dict[str, Dict[str, Any]] = {}

        # 1. Add all Photo 1 confident matches
        for item in photo1_results.get("confident", []):
            sid = item["student_id"]
            confident_by_student[sid] = item

        # 2. Process Photo 2 confident matches
        for item in photo2_results.get("confident", []):
            sid = item["student_id"]
            if sid in confident_by_student:
                # If already confident in photo 1, keep the one with higher score
                if item["confidence_score"] > confident_by_student[sid]["confidence_score"]:
                    confident_by_student[sid] = item
            else:
                # Promotes student from uncertain/not-detected to confident
                confident_by_student[sid] = item

        merged_confident = list(confident_by_student.values())
        confident_student_ids = set(confident_by_student.keys())

        # 3. Aggregate review items (excluding those who became confident in photo 2)
        merged_review = []
        seen_review_faces: Set[str] = set()

        for item in photo1_results.get("review", []):
            cand_id = item.get("candidate_student_id")
            if cand_id not in confident_student_ids:
                merged_review.append(item)
                seen_review_faces.add(item["face_id"])

        for item in photo2_results.get("review", []):
            cand_id = item.get("candidate_student_id")
            if cand_id not in confident_student_ids and item["face_id"] not in seen_review_faces:
                merged_review.append(item)
                seen_review_faces.add(item["face_id"])

        # 4. Aggregate unknown faces from both passes
        merged_unknown = []
        for item in photo1_results.get("unknown", []):
            merged_unknown.append(item)
        for item in photo2_results.get("unknown", []):
            merged_unknown.append(item)

        # 5. Compute true not-detected students across both photos
        merged_not_detected = []
        all_not_detected_candidates = {
            item["student_id"]: item 
            for item in photo1_results.get("not_detected", [])
        }
        # Also check photo 2 not detected
        for item in photo2_results.get("not_detected", []):
            all_not_detected_candidates[item["student_id"]] = item

        for sid, item in all_not_detected_candidates.items():
            if sid not in confident_student_ids:
                merged_not_detected.append(item)

        return {
            "confident": merged_confident,
            "review": merged_review,
            "unknown": merged_unknown,
            "not_detected": merged_not_detected
        }

merge_service = MergeService()
