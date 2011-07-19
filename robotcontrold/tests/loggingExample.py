
import logging

# Log everything, and send it to stderr.
#logging.basicConfig(level=logging.DEBUG)

def g():
    1/0

def f():
    logging.debug("Inside f!")
    try:
        g()
    except Exception as ex:
        logging.exception("Something awful happened!")
    logging.debug("Finishing f!")

if __name__ == "__main__":
    f()
