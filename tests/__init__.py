if __name__ == "__main__":
    import unittest
    # message
    from message.test import *
    from message.payload.test import *

    # event
    from event.test import *

    # board
    from board.test import *
    from board.handler.test import *

    # conn
    from conn.test import *
    from conn.manager.test import *

    # cursor
    from cursor.data.test import *
    from cursor.data.handler.test import *
    from cursor.event.handler.test import *

    unittest.main()
