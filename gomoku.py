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
    board_length = 15
    winning_sequence = 5
    board = []

    def new_websocket_client(self):
        for i in range(1,self.board_length) :
            self.board.append([None] * self.board_length)

        while True:
            ins, outs, excepts = select.select([self.request], [], [], 1)
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
                if items and items['is_black'] != self.im_black :
                    if items['win'] :
                        result = json.dumps({'result': 'oppwin','x':items['x'],'y':items['y']})
                        self.send_frames([str.encode(result)])
                        return
                    self.board[items['y']][items['x']] = not self.im_black
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

                        ## CHECK WINNING MOVE HERE
                        win = False
                        self.board[action['y']][action['x']] = self.im_black
                    
                        if self.checkwinner(action['x'], action['y']) :
                            win = True
                            result = {'result': 'youwin'}
                            self.send_frames([str.encode(json.dumps(result))])

                        cur.execute('INSERT INTO match_moves (match_id, is_black, x, y, win) VALUES (%s,%s,%s,%s,%s) RETURNING made', [self.game_id, self.im_black, action['x'], action['y'], win])
                        con.commit()
                        items = cur.fetchone()
                        self.last_move = items['made']
                        self.total_moves += 1
                        self.waiting_opponent_move = True

                    con.close()

                if closed:
                    self.send_close()

    def checkwinner(self, x, y) :
        #x asis check
        xsum = 1
        xx = x + 1
        while xx < self.board_length :
            if self.board[y][xx] == self.im_black :
                xsum += 1
            else :
                break
            xx += 1

        xx = x - 1
        while xx >= 0 :
            if self.board[y][xx] == self.im_black :
                xsum += 1
            else :
                break
            xx -= 1

        if xsum == self.winning_sequence :
            return True

        #y asis check
        ysum = 1
        yy = y + 1
        while yy < self.board_length :
            if self.board[yy][x] == self.im_black :
                ysum += 1
            else :
                break
            yy += 1

        yy = y - 1
        while yy >= 0 :
            if self.board[yy][x] == self.im_black :
                ysum += 1
            else :
                break
            yy -= 1

        if ysum == self.winning_sequence :
            return True

        #left diagonal check
        ldsum = 1
        yy = y + 1
        xx = x + 1
        while yy < self.board_length and xx < self.board_length :
            if self.board[yy][xx] == self.im_black :
                ldsum += 1
            else :
                break
            yy += 1
            xx += 1

        yy = y - 1
        xx = x - 1
        while yy >= 0 and xx >= 0 :
            if self.board[yy][xx] == self.im_black :
                ldsum += 1
            else :
                break
            yy -= 1
            xx -= 1

        if ldsum == self.winning_sequence :
            return True

        #right diagonal check
        rdsum = 1
        yy = y + 1
        xx = x - 1
        while yy < self.board_length and xx >= 0 :
            if self.board[yy][xx] == self.im_black :
                rdsum += 1
            else :
                break
            yy += 1
            xx -= 1

        yy = y - 1
        xx = x + 1
        while yy >= 0 and xx < self.board_length :
            if self.board[yy][xx] == self.im_black :
                rdsum += 1
            else :
                break
            yy -= 1
            xx += 1

        if rdsum == self.winning_sequence :
            return True



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