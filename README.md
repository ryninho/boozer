# boozer
Advanced search for blazer.  Work in progress.

next steps:
* discovery: click on a table and click on a field in that table to get counts for the last N ordered by created at

"I'd like to click on a table, click on a field in that table and basically see a graph that summarizes what I would get by running:
Select Field, count(*)
From Table
Where created_at > (a date selected automatically to limit the raw result set to a reasonable amount)
group by 1
Order by count desc"

* get blazer id from user's instacart email address
* don't show dropdown on show_queries page
* search by both "from" and "join"
* post is good for writing something, better to use query params
* show recent queries on search page as default
* add navigation links to each page
* make it prettier with bootstrap
* do something awesome with http://www.datatables.net/

faq:
* errno 48 address already in use --> run 'ps -fA | grep python' and kill other processes using the port already

Refactor:
* DRY out the templates
