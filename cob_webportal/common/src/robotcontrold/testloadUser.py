import MySQLdb, pickle

def getCursor():
    conn = MySQLdb.connect("webportal", "root", "rc4", "cob-sim1")
    return conn.cursor()

def user():
    c = getCursor()
    c.execute("SELECT pickledData from users")
    r = c.fetchone()
    c.close()
    return r[0]

def host():
    c = getCursor()
    c.execute("SELECT pickledData from hosts")
    result = c.fetchall()
    hosts = {}
    for row in result:
        h = pickle.loads(row[0])
        h.initializeUnpickableData(log())
        hosts[h.id] = h
    return hosts
    
def log():
    return {'log': lambda(x):x, 'info': lambda(x):x, 'debug': lambda(x): x}
