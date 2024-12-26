import asyncio
import logging
import traceback
import uvicorn
import asyncpg

import utils.log as log
# import os
# import sys
#
# scriptDir = os.path.dirname(os.path.abspath(__file__))
# sys.path.append(scriptDir)
from models import creator

async def main():
    try:
        await creator.create_table()
        # log.critical(
        #     "email_not_found",
        #     "No email was found with this token",
        #     token="token",
        #     func="email_info",
        # )
        # logging.shutdown()
        uvicorn.run('config:app', host='127.0.0.1', port=8000, reload=True)
    except Exception:
        print(traceback.format_exc())


def run_server():
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bye')


if __name__ == '__main__':
    run_server()
