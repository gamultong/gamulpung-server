if __name__ == "__main__":
    import unittest
    # message
    from event.payload.test import *

    # event
    from event.broker.test import *
    from event.message.test import *
    from event.payload.test import *

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

    try:
        unittest.main()
    finally:
        import asyncio
        from db import db
        asyncio.run(db.close())
