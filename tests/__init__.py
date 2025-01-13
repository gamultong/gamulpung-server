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

    # receiver
    # from receiver.board.test import *
    # from receiver.conn.test import *
    # from receiver.cursor.test import *

    try:
        unittest.main()
    finally:
        import asyncio
        from db import db
        asyncio.run(db.close())
