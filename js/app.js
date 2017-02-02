var ws = new Websock();

class GameBoard extends React.Component {
    constructor(props) {
        super(props);

        //connecnting to server
        ws.open("ws://bloges.lan:8888/");

        //creating board
        let tmp = Array(15).fill(null);
        tmp.map(function(i,ind) {
            tmp[ind] = Array(15).fill(null);
        });

        this.state = {
            game_id: null,
            black: '',
            white: null,
            type: 'new',
            turn: null,
            matched: false,
            waiting_opponents_move: true,
            protagonist: 'black',
            antagonist: 'white',
            squares: tmp,
            last_x: null,
            last_y: null
        };
        this.handleSubmit = this.handleSubmit.bind(this);
        this.handleInputChange = this.handleInputChange.bind(this);
    }

    handleInputChange(event) {
        const target = event.target;
        const value = target.type === 'checkbox' ? target.checked : target.value;
        const name = target.name;

        this.setState({
            [name]: value
        });
    }

    handleSubmit(event) {
        event.preventDefault();
        let me = this;
        ws.on('message', function(e) {
            me.handleServerResponce(JSON.parse(ws.rQshiftStr()));
        });

        if (this.state.type == 'new') {
            ws.send_string(JSON.stringify({
                action: "start",
                username: this.state.username
            }));
        } else {
            ws.send_string(JSON.stringify({
                action: "join",
                username: this.state.username,
                game_id: this.state.game_id,
            }));
            this.setState({protagonist: 'white', antagonist: 'black'});
        }

    }

    handleServerResponce(resp) {
        console.log(resp);
        let tmp = this.state.squares;
        switch(resp.result) {
            case 'started' :
                this.setState({matched: true, game_id: resp.game_id, turn: 'Waiting for opponent connection...'});
                break;
            case 'joined' :
                this.setState({matched: true, black: resp.black, white: resp.white, game_id: resp.game_id, turn: 'Waiting for opponent connection...'});
                break;
            case 'matched' :
                this.setState({black: resp.black, white: resp.white, waiting_opponents_move: false, turn: 'Your turn!'});
                break;
            case 'moved' :
                tmp[resp.y][resp.x] = this.state.antagonist;
                this.setState({squares: tmp, last_x: resp.x, last_y: resp.y, waiting_opponents_move: false, turn: 'Your turn!'});
                break;
            case 'youwin' :
                this.setState({waiting_opponents_move: true, turn: '<span style="color:#008000;">You win! =)</span>'});
                break;
            case 'oppwin' :
                tmp[resp.y][resp.x] = this.state.antagonist;
                this.setState({squares: tmp, last_x: resp.x, last_y: resp.y, waiting_opponents_move: true, turn: '<span style="color:#800000;">Your opponent has win. =(</span>'});
                break;
            case 'error' :
                alert(resp.message);
                break;
            default:
                console.log('Unknown result')
        }
    }
  
    clickCell(x,y) {
        if (this.state.waiting_opponents_move) {
            return;
        }
        let tmp = this.state.squares;
        tmp[y][x] = this.state.protagonist;
        ws.send_string(JSON.stringify({
            action: "move",
            color: this.state.protagonist,
            x: x,
            y: y
        }));
        this.setState({squares:tmp, waiting_opponents_move:true, turn: 'Waiting for opponent\'s turn...'});
    }

    componentDidMount() {
        ReactDOM.findDOMNode(this.refs.nameinput).focus();
    }

    render() {
        if (!this.state.matched) {

            return (
            <form className="mui-form" onSubmit={this.handleSubmit}>
                
                <div className="mui-textfield">
                    <input type="text" name="username" placeholder="Your name *" ref="nameinput" value={this.state.username} onChange={this.handleInputChange} />
                </div>

                <div className="mui-textfield">
                    <label>
                    <input type="radio" name="type" value="new" checked={this.state.type=='new'} onChange={this.handleInputChange} />
                    &#160;I want to start a new game
                    </label>
                </div>
                <div className="mui-textfield">
                    <label>
                    <input type="radio" name="type" value="join" checked={this.state.type=='join'} onChange={this.handleInputChange}/>
                    &#160;I want to join existing game
                    </label>
                </div>
                <div className={"mui-textfield " + (this.state.type == 'join' ? '':'none')}>
                    <input type="number" name="game_id" placeholder="Existing game ident" value={this.state.game_id} onChange={this.handleInputChange} />
                </div>
                <button type="submit" className="mui-btn mui-btn--primary" disabled={!this.state.username || (this.state.type=='join' && !this.state.game_id)} >{this.state.type=='join'?'Join':'Create'}</button>
            </form>
            );

        } else {
            let me = this;
            let rows = this.state.squares.map(function(item, index) {
                let cells = item.map(function(subitem, subindex) {
                    return (
                    <td key={subindex} className={subitem ? (me.state.last_y == index && me.state.last_x == subindex ? subitem + " lastmove"  : subitem) : ''} onClick={() => me.clickCell(subindex,index)}><div/></td>
                    )
                });
                return (
                <tr key={index}>
                    {cells}
                </tr>
                )
            });
            return (
                <div>
                    <h5>Match <small>#</small><strong>{this.state.game_id}</strong> {this.state.black}<small> vs </small>{this.state.white ? this.state.white : '?'}</h5>
                    <h6>{this.state.turn}</h6>
                    <table className="board">
                        <tbody>
                            {rows}
                        </tbody>
                    </table>
                </div>
            );
        }
    }
}


var App = React.createClass({
    render: function() {
        return (
        <div>
            <h3>Gomoku prototype</h3>
            <GameBoard />
        </div>
        );
    }
});


ReactDOM.render(
    <App />,
    document.getElementById('root')
);