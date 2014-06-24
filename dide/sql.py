# -*- coding: utf-8 -*-
permanent_post_in_organization = """
SELECT dide_placement.employee_id
FROM dide_placement
INNER JOIN (
    SELECT employee_id, MAX(date_from) AS maxdate
    FROM dide_placement
    WHERE type_id = 1
    GROUP BY employee_id
) AS aggr ON aggr.employee_id=dide_placement.employee_id AND dide_placement.date_from=aggr.maxdate
INNER JOIN dide_permanent ON dide_permanent.parent_id=dide_placement.employee_id
INNER JOIN dide_employee ON dide_employee.id=dide_placement.employee_id
WHERE dide_employee.currently_serves=1 AND dide_permanent.has_permanent_post=1 AND dide_placement.organization_id={0}
"""

permanent_post_in_island = """
SELECT dide_placement.employee_id
FROM dide_placement
INNER JOIN (
    SELECT employee_id, MAX(date_from) AS maxdate, organization_id
    FROM dide_placement
    WHERE type_id = 1
    GROUP BY employee_id
) AS aggr ON aggr.employee_id=dide_placement.employee_id AND dide_placement.date_from=aggr.maxdate
INNER JOIN dide_permanent ON dide_permanent.parent_id=dide_placement.employee_id
INNER JOIN dide_employee ON dide_employee.id=dide_placement.employee_id
INNER JOIN dide_school ON dide_placement.organization_id=dide_school.parent_organization_id
WHERE dide_employee.currently_serves=1 AND dide_permanent.has_permanent_post=1 AND dide_school.island_id={0}
"""

temporary_post_in_organization = """
SELECT dide_placement.employee_id
FROM dide_placement
INNER JOIN (
    SELECT employee_id, MAX(date_from) AS maxdate
    FROM dide_placement
    WHERE type_id = 3
    GROUP BY employee_id
) AS aggr ON aggr.employee_id=dide_placement.employee_id AND dide_placement.date_from=aggr.maxdate
INNER JOIN dide_employee ON dide_employee.id=dide_placement.employee_id
INNER JOIN dide_permanent ON dide_employee.id=dide_permanent.parent_id
WHERE
    dide_employee.currently_serves=1 AND
    dide_placement.organization_id={0} AND
    dide_permanent.has_permanent_post=0
"""

on_service = """
SELECT dide_placement.employee_id
    FROM dide_placement
    WHERE dide_placement.type_id=6
    AND (DATE('{0}') BETWEEN dide_placement.date_from AND dide_placement.date_to)
"""

serving_in_organization = """
SELECT employee_id FROM (
        SELECT dide_placement.employee_id
        FROM dide_placement
        WHERE dide_placement.organization_id = {0} AND dide_placement.type_id IN (2, 3)
        AND (DATE('{1}') BETWEEN dide_placement.date_from AND dide_placement.date_to)

        UNION
""" + permanent_post_in_organization +""") AS fb
WHERE fb.employee_id NOT IN (
    SELECT employee_id FROM (
        SELECT dide_placement.employee_id, max( date_from )
        FROM dide_placement
        WHERE dide_placement.organization_id <> {0}
        AND dide_placement.type_id IN (2, 6, 4)
        AND  (DATE('{1}') BETWEEN dide_placement.date_from AND dide_placement.date_to)
        GROUP BY employee_id
    ) AS foobar
)
UNION
    SELECT dide_placement.employee_id
    FROM dide_placement
    WHERE dide_placement.organization_id = {0}
          AND dide_placement.type_id IN ( 4, 6 )
          AND (DATE('{1}') BETWEEN dide_placement.date_from  AND dide_placement.date_to )
"""

serving_in_island = """
SELECT employee_id FROM (
        SELECT dide_placement.employee_id
        FROM dide_placement
        INNER JOIN dide_school ON dide_school.parent_organization_id=dide_placement.organization_id
        WHERE dide_school.island_id = {0} AND dide_placement.type_id IN (2, 3)
        AND (DATE('{1}') BETWEEN dide_placement.date_from AND dide_placement.date_to)

        UNION
""" + permanent_post_in_island +""") AS fb
WHERE fb.employee_id NOT IN (
    SELECT employee_id FROM (
        SELECT dide_placement.employee_id, max( date_from )
        FROM dide_placement
        LEFT OUTER JOIN dide_school ON dide_school.parent_organization_id=dide_placement.organization_id
        WHERE (dide_school.island_id IS NULL OR dide_school.island_id <> {0})
        AND dide_placement.type_id IN (2, 6, 4)
        AND  (DATE('{1}') BETWEEN dide_placement.date_from AND dide_placement.date_to)
        GROUP BY employee_id
    ) AS foobar
)
UNION
    SELECT dide_placement.employee_id
    FROM dide_placement
    INNER JOIN dide_school ON dide_school.parent_organization_id=dide_placement.organization_id
    WHERE dide_school.island_id = {0}
          AND dide_placement.type_id IN ( 4, 6 )
          AND (DATE('{1}') BETWEEN dide_placement.date_from  AND dide_placement.date_to )
"""

serves_in_dide_school = """
SELECT dide_permanent.parent_id
FROM dide_permanent
WHERE dide_permanent.parent_id NOT
IN (
    SELECT dide_placement.employee_id
    FROM dide_permanent
    INNER JOIN dide_placement ON dide_permanent.parent_id = dide_placement.employee_id
    INNER JOIN dide_otherorganization ON dide_otherorganization.parent_organization_id = dide_placement.organization_id
    WHERE DATE('{0}') BETWEEN dide_placement.date_from AND dide_placement.date_to
)
"""

serves_in_other_org = """
SELECT dide_placement.employee_id
FROM dide_placement
INNER JOIN (
    SELECT MAX( date_from ) AS maxdate, employee_id
    FROM dide_placement
    GROUP BY employee_id
) AS foo ON foo.maxdate = dide_placement.date_from AND foo.employee_id = dide_placement.employee_id
INNER JOIN dide_organization ON dide_organization.id = dide_placement.organization_id
WHERE (DATE('{0}') BETWEEN dide_placement.date_from AND dide_placement.date_to)
AND dide_organization.belongs = 0
"""

current_year_non_permanents = """
SELECT dide_employee.id, dide_employee.lastname, dide_employee.firstname, dide_employee.vat_number
FROM `dide_nonpermanent`
INNER JOIN dide_placement ON dide_nonpermanent.parent_id = dide_placement.employee_id
INNER JOIN dide_employee ON dide_nonpermanent.parent_id = dide_employee.id
WHERE dide_placement.date_from >= DATE( '{0}' )
ORDER BY lastname, firstname
"""
