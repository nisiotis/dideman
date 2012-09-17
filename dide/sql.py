# -*- coding: utf-8 -*-
permanent_post_in_organization = """
SELECT dide_employee.id
FROM dide_employee
     INNER JOIN (
           SELECT employee_id, organization_id, max( date_from )
            FROM (
                SELECT dide_placement.*
                FROM dide_placement
                WHERE type_id = 1
                ORDER BY date_from DESC
            ) AS foo
            GROUP BY employee_id
     ) AS bar
         ON dide_employee.id = bar.employee_id
WHERE dide_employee.currently_serves = 1 and bar.organization_id={0}
"""

serving_in_organization = """
SELECT employee_id FROM (
        SELECT dide_placement.employee_id
        FROM dide_placement
        WHERE dide_placement.organization_id = {0}
        AND dide_placement.type_id = 6
        AND (
            (DATE('{1}') BETWEEN dide_placement.date_FROM AND dide_placement.date_to)
            OR
            (DATE('{2}') BETWEEN dide_placement.date_FROM AND dide_placement.date_to)
        )

        UNION

        SELECT dide_placement.employee_id
        FROM dide_placement
        WHERE dide_placement.organization_id = {0} AND dide_placement.type_id IN (2, 3)
        AND dide_placement.date_FROM >= DATE('{1}')
        AND (
            dide_placement.date_to <= DATE('{2}') OR
            dide_placement.date_to IS NULL
        )

        UNION
""" + permanent_post_in_organization +""") AS fb
WHERE fb.employee_id NOT IN (
    SELECT employee_id FROM (
        SELECT dide_placement.employee_id, max( date_FROM )
        FROM dide_placement
        WHERE dide_placement.organization_id <> {0}
        AND dide_placement.type_id IN (2, 6)
        AND  (
                (DATE('{1}') BETWEEN dide_placement.date_FROM AND dide_placement.date_to)
                OR
                (DATE('2012-08-31') BETWEEN dide_placement.date_FROM AND dide_placement.date_to)
                OR
                (dide_placement.date_to <= DATE('{2}') OR
                dide_placement.date_to IS NULL)
             )
        GROUP BY employee_id
    ) AS foobar
)
"""
serves_in_dide_school = """
SELECT dide_permanent . parent_id
FROM dide_permanent
WHERE dide_permanent.parent_id NOT
IN (
    SELECT dide_placement.employee_id
    FROM dide_permanent
    INNER JOIN dide_placement ON dide_permanent.parent_id = dide_placement.employee_id
    INNER JOIN dide_otherorganization ON dide_otherorganization.parent_organization_id = dide_placement.organization_id
    WHERE dide_placement.date_from >=  '{0}' and dide_placement.date_to <= '{1}'
)"""
