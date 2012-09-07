# -*- coding: utf-8 -*-
permanent_post_in_organization = """
SELECT dide_employee.id
FROM dide_employee
     INNER JOIN (
           SELECT employee_id, organization_id, max( date_from )
            FROM (
                SELECT dide_placement.*
                FROM dide_placement
                INNER JOIN dide_placementtype ON dide_placementtype.id = dide_placement.type_id
                WHERE dide_placementtype.id = 1
                ORDER BY date_from DESC
            ) AS foo
            GROUP BY employee_id
     ) AS bar
         ON dide_employee.id = bar.employee_id
WHERE dide_employee.currently_serves = 1 and bar.organization_id={0}
"""

serving_in_organization = """
SELECT * FROM (
    SELECT dide_employee.id
    FROM dide_permanent
    INNER JOIN (
        SELECT dide_placement.*
        FROM dide_placement
        INNER JOIN
            dide_placementtype AS t
                ON dide_placement.type_id = t.id
        INNER JOIN dide_organization
            ON dide_organization.id = dide_placement.organization_id
        WHERE t.id IN (2,3,6)  /* apospasi, prosorini, thitia */
            AND dide_organization.id = {0}
            AND dide_placement.date_from >= DATE('{1}')
            AND (
                  dide_placement.date_to <= DATE('{2}') OR
                  dide_placement.date_to IS NULL
            )
    ) as foo ON foo.employee_id = dide_permanent.parent_id
    INNER JOIN
        dide_employee ON
            dide_employee.id = dide_permanent.parent_id
        WHERE dide_employee.currently_serves = 1
    UNION(""" + permanent_post_in_organization + """ )
) as foobar
    WHERE foobar.id NOT IN ( /*  meion aytoi poy exoyn parei apospasi h thiteia allou */
        SELECT dide_employee.id
        FROM dide_employee
        INNER JOIN (
                SELECT employee_id, organization_id, max( date_from )  /* teleftaia topothetisi organikon kai prosorinwn */
                FROM (
                   SELECT dide_placement. *   /* organikoi kai prosorinoi sto sxoleio */
                   FROM dide_placement
                   INNER JOIN
                        dide_placementtype AS t
                            ON dide_placement.type_id = t.id
                    WHERE dide_placement.organization_id = {0}
                        AND t.id IN (1, 3) /* organiki, prosorini */
                    ORDER BY date_from DESC
                ) AS p
                GROUP BY p.employee_id
                ORDER BY employee_id
         ) AS foo
             ON dide_employee.id = foo.employee_id
        INNER JOIN(
            SELECT dide_placement.*  /* aytoi poy exoyn parei apospasi h thiteia */
            FROM dide_placement
            INNER JOIN
                dide_placementtype AS t
                    ON dide_placement.type_id = t.id
            INNER JOIN dide_organization
                ON dide_organization.id = dide_placement.organization_id
            WHERE t.id IN (2, 6)
                AND dide_placement.date_from >= DATE('{1}')
                OR dide_placement.date_to >= DATE('{1}')
        ) AS bar ON bar.employee_id = dide_employee.id
        WHERE dide_employee.currently_serves = 1
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
