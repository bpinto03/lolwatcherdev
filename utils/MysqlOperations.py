import os
import psycopg2

def connect_database():
    """Connect to the database linked to Lol tracker application

    Returns:
       psycopg2.extensions.connection : Connection of database.
    """
    cnx = None
    try:
        #cnx = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require') For prod
        cnx = psycopg2.connect('postgres://yqxyjdvhlludxc:11c7535b4faf8cc2fcc2e1531e76408b5b3145ca42ad80fd3568fe2c48d07c88@ec2-54-77-90-39.eu-west-1.compute.amazonaws.com:5432/d9b8m8at40psv0', sslmode='require')

    except Exception as e:
        print(e)
    return cnx

def select_values_from_table(cnx : psycopg2.extensions.connection, table_name : str, values : list, conditions : str = None):
    """Make a selected request to get 'values' in 'table_name' with conditions.

    Args:
        cnx (psycopg2.extensions.connection): Connexion of database.
        table_name (str): Table where we want to make SELECT request.
        values (list): values is a list of str. (EXAMPLE: SELECT id, nom, age FROM table_name  => values = ['id', 'nom', 'age'])
        conditions (str, optional): String condition to apply to the request. (EXAMPLE: conditions = 'nom = 'Pierre' AND age = 18') Defaults to None.

    Returns:
        list : List of dictionnaries with results. (EXAMPLE: [{'id': 1, 'nom':'Pierre', 'age':18}, {'id': 2, 'nom':'Pierre', 'age':18}, ...])
    """
    cnx = connect_database()
    cursor = cnx.cursor()
    values_sql = ", ".join(values)
    try:
        if conditions != None:
            cursor.execute("SELECT {0} FROM {1} WHERE {2}".format(values_sql, table_name, conditions))
        else:
            cursor.execute("SELECT {0} FROM {1}".format(values_sql, table_name))
    except Exception as e:
        print(e)
        cursor.close()
        return dict()
    res = cursor.fetchall()
    cursor.close()
    return res

def add_values_on_table(cnx : psycopg2.extensions.connection, table_name : str, values : list):
    """Make an INSERT request with 'values' in 'table_name'.
    Args:
        cnx (psycopg2.extensions.connection): Connexion of database.
        table_name (str): Table where we want to make INSERT request. 
        values (list): values is a list with all values to add. (EXEMPLE: INSERT INTO 'table_name' VALUES ('a', 4) => values = ['a', 4])

    Returns:
        boolean: True if values are added else False.
    """
    cursor = cnx.cursor()
    values_sql = ", ".join(["'"+ value + "'" for value in values])
    try:
        cursor.execute("INSERT INTO {0} VALUES ({1})".format(table_name, values_sql))
    except Exception as e:
        print(e)
        cursor.close()
        return False
    cnx.commit()
    cursor.close()
    return True

def update_values_on_table(cnx : psycopg2.extensions.connection, table_name : str, replace_value_instr : list, condition : str = None):
    """Make an update request with 'replace_value_instr' in table 'table_name' with condition 'condition'.

    Args:
        cnx (psycopg2.extensions.connection): Connexion of database.
        table_name (str): Table where we want to make INSERT request.
        replace_value_instr (list): Instruction for replace (EXAMPLE: "age = 28")
        condition (str, optional): String condition to apply to the request.(EXAMPLE: "nom = 'PIERRE'"). Defaults to None.

    Returns:
        boolean: True if values are updated else False.
    """
    cursor = cnx.cursor()
    try:
        if condition != None:
            cursor.execute("UPDATE {0} SET {1} WHERE {2}".format(table_name, replace_value_instr, condition))
        else:
             cursor.execute("UPDATE {0} SET {1}".format(table_name, replace_value_instr))
    except Exception as e:
        print(e)
        cursor.close()
        return False
    cnx.commit()
    cursor.close()
    return True

def delete_values_on_table(cnx : psycopg2.extensions.connection, table_name : str, condition : str = None):
    """Make an delete request in table 'table_name' with condition 'condition'.

    Args:
        cnx (psycopg2.extensions.connection): Connexion of database.
        table_name (str): Table where we want to make INSERT request.
        replace_value_instr (list): Instruction for replace (EXAMPLE: "age = 28")
        condition (str, optional): String condition to apply to the request.(EXAMPLE: "nom = 'PIERRE'"). Defaults to None.

    Returns:
        boolean: True if values are updated else False.
    """
    cursor = cnx.cursor()
    try:
        if condition != None:
            cursor.execute("DELETE FROM {0} WHERE {1}".format(table_name, condition))
        else:
            cursor.execute("DELETE FROM {0}")
    except Exception as e:
        print(e)
        cursor.close()
        return False
    cnx.commit()
    cursor.close()
    return True