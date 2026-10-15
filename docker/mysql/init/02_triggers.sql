/*
==============================================
MySQL VERSION
==============================================
Created by: Roselie Freixas
Last modified by: Roselie Freixas
CS 458 - Software Engineering
Version - v0.5
Last Modified: 05-OCT-2026

FILE 2 of 5: IMPLEMENT TRIGGERs

Run this AFTER 01_schema_setup.sql
==============================================
*/

/*
===============================================================================
Trigger 'category_parent_before_insert' validates new category_parent relationships
before they are inserted
- skill_id: must reference a category with category_type 'skill'
- parent_id: must reference a category with category_type 'degree program'
             or 'career field'
- invalid relationships are rejected before insertion
===============================================================================
*/
drop trigger if exists category_parent_before_insert;
drop trigger if exists category_parent_before_update;

delimiter //

create trigger category_parent_before_insert
before insert on category_parent
for each row
begin
    declare skill_type varchar(20);
    declare parent_type varchar(20);

    select category_type into skill_type
    from category
    where category_id = new.skill_id;

    select category_type into parent_type
    from category
    where category_id = new.parent_id;

    if skill_type <> 'skill' then
        signal sqlstate '45000'
            set message_text = 'skill_id must reference a skill category';
    end if;

    if parent_type not in ('degree program', 'career field') then
        signal sqlstate '45000'
            set message_text = 'parent_id must reference a degree program or career field category';
    end if;
end//


/*
===============================================================================
Trigger 'category_parent_before_update' validates changes to existing
category_parent relationships before they are updated
- skill_id: must reference a category with category_type 'skill'
- parent_id: must reference a category with category_type 'degree program'
             or 'career field'
- invalid relationship changes are rejected before update
===============================================================================
*/

create trigger category_parent_before_update
before update on category_parent
for each row
begin
    declare skill_type varchar(20);
    declare parent_type varchar(20);

    select category_type into skill_type
    from category
    where category_id = new.skill_id;

    select category_type into parent_type
    from category
    where category_id = new.parent_id;

    if skill_type <> 'skill' then
        signal sqlstate '45000'
            set message_text = 'skill_id must reference a skill category';
    end if;

    if parent_type not in ('degree program', 'career field') then
        signal sqlstate '45000'
            set message_text = 'parent_id must reference a degree program or career field category';
    end if;
end//

delimiter ;
