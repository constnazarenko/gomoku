
class GameBoard extends React.Component {
  constructor(props) {
    let tmp = Array(15).fill(null);
    tmp.map(function(i,ind) {
        tmp[ind] = Array(15).fill(null);
    });
    
    super(props);
    this.state = {
        username: '',
        type: 'new',
        ident: 12345,
        matched: false,
        color: 'b',
        opponent_name: null,
        opponent_color: 'w',
        waiting_opponents_move: false,
        squares: tmp,
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
    //Connect to server here
    this.setState({matched:true});
  }

  componentDidMount() {
    ReactDOM.findDOMNode(this.refs.nameinput).focus();
  }
  
  clickCell(x,y) {
      if (this.state.waiting_opponents_move) {
          return;
      }
      let tmp = this.state.squares;
      tmp[y][x] = this.state.color;
      this.setState({squares:tmp, waiting_opponents_move:true});
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
                &#160;I want to start new game
                </label>
            </div>
            <div className="mui-textfield">
                <label>
                <input type="radio" name="type" value="join" checked={this.state.type=='join'} onChange={this.handleInputChange}/>
                &#160;I want to join existing game
                </label>
            </div>
            <div className={"mui-textfield " + (this.state.type == 'join' ? '':'none')}>
                <input type="text" name="ident" placeholder="Existing game ident" value={this.state.ident} onChange={this.handleInputChange} />
            </div>
            <button type="submit" className="mui-btn mui-btn--primary" disabled={!this.state.username || (this.state.type=='join' && !this.state.ident)} >{this.state.type=='join'?'Join':'Create'}</button>
        </form>
        );

      } else {

          let me = this;

            let rows = this.state.squares.map(function(item, index) {

                let cells = item.map(function(subitem, subindex) {
                    return (
                    <td key={subindex} className={subitem == 'b' ? 'black' : (subitem == 'w' ? 'white' : '')} onClick={() => me.clickCell(subindex,index)}><div/></td>
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
                <h5>Match <small>#</small><strong>{this.state.ident}</strong> {this.state.username}<small> vs </small>{this.state.opponent_name ? this.state.opponent_name : '?'}</h5>
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