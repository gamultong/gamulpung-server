if __name__ == "__main__":
    import unittest
    # message
    from message.test import *
    from message.payload.test import *

    # event
    from event.test import *

    # board
    from board.data.test import *
    from board.data.storage.test import *
    from board.data.handler.test import *
    from board.event.handler.test import *

    # conn
    from conn.test import *
    from conn.manager.test import *

    # cursor
    from cursor.data.test import *
    from cursor.data.handler.test import *
    from cursor.event.handler.test import *

    unittest.main()
