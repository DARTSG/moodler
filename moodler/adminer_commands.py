"""
This file will contain all the functionality to be called from the adminer
interface in the Moodle UI.
"""
import re

from moodler.config import URL
from moodler.moodle_exception import MoodlerException

DB_UPDATE_SQL_COMMAND = r"""
DELIMITER //

DROP PROCEDURE IF EXISTS Update_feedback;

CREATE PROCEDURE Update_feedback()
BEGIN

	DECLARE current_row INT;
	SET current_row = 0;
   
	SET @i=0;
   
	CREATE TEMPORARY TABLE new_feedback
	SELECT @i:=@i+1 As RowId, A.commenttext, D.feedback, D.itemid, D.userid
	FROM mdl_assignfeedback_comments A
	LEFT JOIN mdl_assign_grades B ON A.grade = B.id
	LEFT JOIN mdl_grade_items C ON B.assignment = C.iteminstance
	LEFT JOIN mdl_grade_grades D ON c.id= d.itemid AND B.userid = D.userid
	WHERE A.commenttext <> '' AND A.commenttext IS NOT NULL 
                                  AND A.commenttext <> '0' 
                                  AND (A.commenttext <> D.feedback OR D.feedback IS NULL)
                                  AND C.id= D.itemid 
                                  AND B.userid = D.userid;



	SELECT MAX(RowId) INTO @max FROM new_feedback;
   
	label1: LOOP


		SELECT itemid, userid, commenttext
		 INTO @assignment, @userid, @feedback
		 FROM new_feedback
		 WHERE RowId = current_row;

		UPDATE mdl_grade_grades
		SET feedback = @feedback
		WHERE itemid = @assignment AND userid = @userid;
		 
		SET current_row = current_row + 1;
		IF current_row <= @max THEN
			ITERATE label1;
		END IF;
		LEAVE label1;
	END LOOP label1;
END; //
DELIMITER ;

call Update_feedback()
"""

TOKEN_PATTERN = (
    r'form action=[\'"]{2} method=[\'"]{1}post[\'"]{1}.*name=['
    r'\'"]{1}token[\'"]{1} value=[\'"]{1}([\d:]+)[\'"]{1}'
)
RESPONSE_RESULT_PATTERN = r"Query executed OK, (\d+) rows affected."
DB_NAME = "bitnami_moodle"
ADMINER_PAGE = "/local/adminer/lib/run_adminer.php"


class AdminerException(MoodlerException):
    pass


class SQLCommandException(AdminerException):
    pass


class SQLTokenNotFound(SQLCommandException):
    pass


class SQLNoRowBeenAffected(SQLCommandException):
    pass


def get_sql_command_token(session):
    """
    Function to find the token that allows to run an SQL command.
    :param session: The session object that allows to send requests to the
    Moodle server.
    :return: The value of the token for the SQL command.
    """
    params = {"server": "", "username": "", "db": DB_NAME, "sql": ""}
    response = session.get(URL + ADMINER_PAGE, params=params)

    token_match = re.search(TOKEN_PATTERN, response.content.decode(), re.DOTALL)

    if token_match is None:
        raise SQLTokenNotFound(
            "The SQL command requires a token to be "
            "received from the server, but in this case "
            "the token was not found. It could be that the "
            "server has changed the implementation and the "
            "token can only be found elsewhere"
        )

    return token_match.group(1)


def run_sql_command_using_token(session, token_value, sql_command):
    """
    Function to run an SQL command on the Moodle server on the DB for report.
    :param session: The session object that allows to send requests to the
    Moodle server.
    :param token_value: The value of the token to be used for the SQL command
    sending.
    :param sql_command: The SQL command to run on the DB for reports in the
    Moodle.
    :return:
    """
    params = {"server": "", "username": "", "db": DB_NAME, "sql": ""}
    files = {
        "query": (None, sql_command),
        "limit": (None, ""),
        "token": (None, token_value),
    }
    response = session.post(URL + "/local/adminer/lib/run_adminer.php", params=params, files=files)

    rows_affected_counts = re.findall(RESPONSE_RESULT_PATTERN, response.content.decode())

    # Making sure there is at least one row affected by the query
    if not any(map(int, rows_affected_counts)):
        raise SQLNoRowBeenAffected(
            "The response for the SQL command has "
            "returned that the command did not affect "
            "any value in the DB"
        )


def run_reports_db_sql_command(session, sql_command):
    """
    Function to run an SQL command on the reports DB.
    :param session: The session object that allows to send requests to the
    Moodle server.
    :param sql_command: The SQL command to use for the DB.
    :return:
    """
    token_value = get_sql_command_token(session)
    run_sql_command_using_token(session, token_value, sql_command)


def update_reports_db(session):
    """
    Function that updates the reports DB to the lastest data in the Moodle
    using an SQL command.
    :param session: The session object that allows to send requests to the
    Moodle server.
    :return:
    """
    run_reports_db_sql_command(session, DB_UPDATE_SQL_COMMAND)
