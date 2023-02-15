# dideman
Database system for greek secondary education administration. Written in python django

The system covers extensive administrative requirements for a directorate of secondary education. 
It has a back end for the administrative personnel, with the ability to allocate services for every 
teacher and a front end for the teacher to have access to his/her details, including leave time, 
serving positions and financial history. 

The django platform requires a linux server and a wsgi-capable web server. As for the system to work, 
it requires a MySQL database and a long list of python libraries, such as ReportLab pdf engine, Pandas 
statistics, PIL image and a caching engine, johnny-cache.

New version in new_version branch for django 1.7.11 including a somewhat new interface.
