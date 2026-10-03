#!/usr/bin/env bash
# End-to-end walkthrough of every use case against a running API.
# Usage: ./scripts/demo.sh [base_url]   (default: http://localhost:8000)
set -euo pipefail

BASE="${1:-http://localhost:8000}/api/v1"
RUN_ID="$(date +%s)"
OWNER="ana.${RUN_ID}@example.com"
ASSIGNEE="bob.${RUN_ID}@example.com"
PASSWORD="supersecret1"

json() { python3 -c "import json, sys; print(json.load(sys.stdin)$1)"; }
show() { python3 -m json.tool; }
step() { printf '\n\033[1;34m== %s\033[0m\n' "$1"; }
call() { curl -sS -H "Content-Type: application/json" "$@"; }

step "1. Register two users"
call -X POST "$BASE/auth/register" -d "{\"email\":\"$OWNER\",\"password\":\"$PASSWORD\",\"full_name\":\"Ana Torres\"}" | show
call -X POST "$BASE/auth/register" -d "{\"email\":\"$ASSIGNEE\",\"password\":\"$PASSWORD\",\"full_name\":\"Bob Ruiz\"}" > /dev/null

step "2. Log in (JWT)"
OWNER_TOKEN=$(curl -sS -X POST "$BASE/auth/login" -d "username=$OWNER&password=$PASSWORD" | json '["access_token"]')
ASSIGNEE_TOKEN=$(curl -sS -X POST "$BASE/auth/login" -d "username=$ASSIGNEE&password=$PASSWORD" | json '["access_token"]')
AUTH=(-H "Authorization: Bearer $OWNER_TOKEN")
echo "Token: ${OWNER_TOKEN:0:40}..."

step "3. Create, get and rename a task list"
LIST_ID=$(call -X POST "$BASE/lists" "${AUTH[@]}" -d '{"name":"Product launch"}' | json '["id"]')
call -X PATCH "$BASE/lists/$LIST_ID" "${AUTH[@]}" -d '{"name":"Product launch Q4"}' | show

step "4. Create tasks with different priorities"
DEMO_ID=$(call -X POST "$BASE/lists/$LIST_ID/tasks" "${AUTH[@]}" -d '{"title":"Prepare demo","priority":"URGENT"}' | json '["id"]')
DOCS_ID=$(call -X POST "$BASE/lists/$LIST_ID/tasks" "${AUTH[@]}" -d '{"title":"Write docs","priority":"HIGH"}' | json '["id"]')
call -X POST "$BASE/lists/$LIST_ID/tasks" "${AUTH[@]}" -d '{"title":"Order snacks","priority":"LOW"}' > /dev/null
echo "Created 3 tasks"

step "5. Update a task (PATCH) and change its status"
call -X PATCH "$BASE/tasks/$DOCS_ID" "${AUTH[@]}" -d '{"description":"README and decision log"}' > /dev/null
call -X PUT "$BASE/tasks/$DEMO_ID/status" "${AUTH[@]}" -d '{"status":"COMPLETED"}' | show

step "6. List tasks filtered by status, with the completion of the whole list"
call "$BASE/lists/$LIST_ID/tasks?status=PENDING" "${AUTH[@]}" | show

step "7. List tasks filtered by priority"
call "$BASE/lists/$LIST_ID/tasks?priority=HIGH" "${AUTH[@]}" | json '["items"][0]["title"]'

step "8. Assign a task by email (a simulated email is logged by the API)"
call -X PUT "$BASE/tasks/$DOCS_ID/assignee" "${AUTH[@]}" -d "{\"email\":\"$ASSIGNEE\"}" | json '["assignee_id"]'

step "9. The assignee sees the task and moves it forward"
call "$BASE/users/me/tasks" -H "Authorization: Bearer $ASSIGNEE_TOKEN" | json '["pagination"]'
call -X PUT "$BASE/tasks/$DOCS_ID/status" -H "Authorization: Bearer $ASSIGNEE_TOKEN" -d '{"status":"IN_PROGRESS"}' | json '["status"]'

step "10. Business errors use Problem Details"
echo "The assignee cannot edit the task (403):"
call -X PATCH "$BASE/tasks/$DOCS_ID" -H "Authorization: Bearer $ASSIGNEE_TOKEN" -d '{"title":"Mine now"}' | show
echo "The assignee cannot see the list (404):"
call "$BASE/lists/$LIST_ID" -H "Authorization: Bearer $ASSIGNEE_TOKEN" | show

step "11. Delete a task and the list (204)"
curl -sS -o /dev/null -w "DELETE task -> %{http_code}\n" -X DELETE "$BASE/tasks/$DEMO_ID" "${AUTH[@]}"
curl -sS -o /dev/null -w "DELETE list -> %{http_code}\n" -X DELETE "$BASE/lists/$LIST_ID" "${AUTH[@]}"
curl -sS -o /dev/null -w "GET deleted list -> %{http_code}\n" "$BASE/lists/$LIST_ID" "${AUTH[@]}"

printf '\nDone. See the simulated email with: docker compose logs api | grep -A6 "Simulated email"\n'
