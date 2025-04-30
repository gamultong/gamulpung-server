if __name__ == "__main__":
    import unittest
    # message
    from event.payload.test import *

    # event
    from event.broker.test import *
    from event.message.test import *
    from event.payload.test import *

    # data
    from data.board.test import *
    from data.conn.test import *
    from data.cursor.test import *

    # handler
    from handler.board.test import *
    from handler.board.storage.test import *
    from handler.cursor.test import *
    from handler.conn.test import *
    from handler.score.test import *

    from handler.storage.dict.test import *
    from handler.storage.list.array.test import *

    # receiver
    from receiver.test import *

    unittest.main()
