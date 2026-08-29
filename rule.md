# Backend Development Rules

1. Commit and push only in small increments.
   - Prefer small feature additions, bug fixes, and test updates over large batch changes.
   - Do not create an entire feature or a large set of files and then commit everything at once.
   - Before every commit and push, ask for permission first:
     - "I added this change and want to commit and push it to GitHub. Is that okay?"
   - Only commit and push after explicit approval from the user.

2. Follow commit prefix rules.
   - Use conventional commit prefixes such as:
     - feat: for new features
     - fix: for bug fixes
     - refactor: for code cleaning or restructuring
     - chore: for maintenance work
     - test: for test additions or fixes
     - docs: for documentation updates
     - perf: for performance improvements
     - ci: for CI configuration changes

3. Use the required commit format.
   - Always use a title and a description separated with two `-m` flags.
   - Example:
     ```bash
     git commit -m "feat: add user validation" -m "Validate email and password fields before creating a user account."
     ```
   - Keep the subject concise and meaningful, and place the detailed explanation in the description.

4. Never bypass these rules during backend development.
   - Small commits only.
   - Permission before commit and push.
   - Proper commit prefixes.
   - Correct two-message commit format.

5. Push policy.
   - Do not push to GitHub without the user's explicit permission.
   - If a user says yes, then push only the small validated change that was approved.
