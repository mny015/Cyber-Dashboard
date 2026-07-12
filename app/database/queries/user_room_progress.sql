SELECT
    (SELECT COUNT(*)
     FROM lab_references AS labs
     JOIN users AS owners ON owners.id = labs.owner_id
     WHERE labs.is_deleted = 0
       AND (labs.owner_id = %(user_id)s OR (labs.visibility = 'public' AND owners.role = 'admin'))) AS total_rooms,
    (SELECT COUNT(DISTINCT completions.lab_id)
     FROM lab_completions AS completions
     JOIN lab_references AS labs ON labs.id = completions.lab_id
     JOIN users AS owners ON owners.id = labs.owner_id
     WHERE completions.user_id = %(user_id)s
       AND labs.is_deleted = 0
       AND (labs.owner_id = %(user_id)s OR (labs.visibility = 'public' AND owners.role = 'admin'))) AS completed_rooms
