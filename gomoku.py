#!/usr/bin/env python

import os, sys, select, optparse, logging, json, psycopg2, psycopg2.extras
sys.path.insert(0,os.path.join(os.path.dirname(__file__), ".."))
from websockify.websocket import WebSocketServer, WebSocketRequestHandler

class Gomoku(WebSocketRequestHandler):
    im_black = True
    last_move = None
    game_id = None
    waiting_opponent_connect = False
    waiting_opponent_move = False
    total_moves = 0

    def new_websocket_client(self):
        rlist = [self.request]
        
        while True:

            wlist = []
            ins, outs, excepts = select.select(rlist, wlist, [], 1)
            if excepts: raise Exception("Socket exception")

            #waiting_opponent_connect check
            if self.waiting_opponent_connect :
                con = psycopg2.connect('dbname=gomoku user=const')
                cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute('SELECT * FROM match WHERE white IS NOT NULL AND id = %s', [self.game_id,])
                items = cur.fetchone()
                if items :
                    result = json.dumps({'result': 'matched','game_id':items['id'],'black':items['black'],'white':items['white']})
                    self.send_frames([str.encode(result)])
                    self.waiting_opponent_connect = False
                con.close()

            #waiting_opponent_move check
            if self.waiting_opponent_move :
                con = psycopg2.connect('dbname=gomoku user=const')
                cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cur.execute('SELECT * FROM match_moves WHERE match_id = %s ORDER BY made DESC LIMIT 1', [self.game_id,])
                items = cur.fetchone()
                if items and items['is_black'] != self.im_black:
                    result = json.dumps({'result': 'moved','x':items['x'],'y':items['y']})
                    self.send_frames([str.encode(result)])
                    self.waiting_opponent_move = False
                    self.total_moves += 1
                con.close()
 
            #if we have recieved something
            if self.request in ins:
                frames, closed = self.recv_frames()
                for f in frames :
                    #parsing actions
                    action = json.loads(f.decode('utf-8'))

                    #connecting to db
                    con = psycopg2.connect('dbname=gomoku user=const')
                    cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                    #starting game
                    if action['action'] == 'start' :

                        cur.execute('INSERT INTO match (black) VALUES (%s) RETURNING id', [action['username'],])
                        con.commit()
                        items = cur.fetchone()

                        result = json.dumps({'result': 'started','game_id':items['id'],'black':action['username']})
                        self.send_frames([str.encode(result)])

                        self.waiting_opponent_connect = True
                        self.game_id = items['id']

                    #joining to existing game
                    if action['action'] == 'join' :

                        cur.execute('SELECT * FROM match WHERE white IS NULL AND id = %s', [action['game_id'],])
                        items = cur.fetchone()

                        if items :
                            cur.execute('UPDATE match SET white = %s WHERE id = %s', [action['username'], items['id']])
                            con.commit()
                            self.im_black = False
                            self.waiting_opponent_move = True
                            self.game_id = items['id']
                            self.last_move = items['start_time']
                            result = {'result': 'joined', 'game_id':items['id'], 'black':items['black'], 'white':action['username']}
                        else :
                            result = {'result': 'error', 'message':'There is no accessible game with such ID.'}
                        self.send_frames([str.encode(json.dumps(result))])

                    #making a move
                    if action['action'] == 'move' :
                        cur.execute('INSERT INTO match_moves (match_id, is_black, x, y) VALUES (%s,%s,%s,%s) RETURNING made', [self.game_id, self.im_black, action['x'], action['y']])
                        con.commit()
                        items = cur.fetchone()
                        self.last_move = items['made']
                        self.total_moves += 1
                        self.waiting_opponent_move = True

                        ## CHECK WINNING MOVE HERE

                    con.close()

                if closed:
                    self.send_close()

if __name__ == '__main__':
    parser = optparse.OptionParser(usage="%prog [options] listen_port")
    parser.add_option("--verbose", "-v", action="store_true",
            help="verbose messages and per frame traffic")
    parser.add_option("--cert", default="self.pem",
            help="SSL certificate file")
    parser.add_option("--key", default=None,
            help="SSL key file (if separate from cert)")
    parser.add_option("--ssl-only", action="store_true",
            help="disallow non-encrypted connections")
    (opts, args) = parser.parse_args()

    try:
        if len(args) != 1: raise
        opts.listen_port = int(args[0])
    except:
        parser.error("Invalid arguments")

    logging.basicConfig(level=logging.INFO)

    opts.web = "."
    server = WebSocketServer(Gomoku, **opts.__dict__)
    server.start_server()