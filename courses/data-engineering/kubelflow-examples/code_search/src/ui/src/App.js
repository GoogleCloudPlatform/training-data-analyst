import React, { Component } from 'react';
import TextField from '@material-ui/core/TextField';
import Button from '@material-ui/core/Button';
import LinearProgress from '@material-ui/core/LinearProgress';
import { MuiThemeProvider } from '@material-ui/core/styles';
import SearchIcon from '@material-ui/icons/Search';

import blueTheme from './theme';
import logo from './logo.svg';
import './App.css';
import CodeSample from './CodeSample';
import code_search_api from './CodeSearchApi';

class App extends Component {
  state = {
    codeResults: [],
    queryStr: '',
    loading: false,
  };

  render() {
    const {codeResults, loading} = this.state;
    return (
      <MuiThemeProvider theme={blueTheme}>
        <div className="App">
          <header className="App-header">
            <img src={logo} className="App-logo" alt="logo" />
            <h1 className="App-title">Code Search Demo</h1>
          </header>
            <div className="Search-Wrapper">
              <TextField
                id="Search-Bar"
                placeholder="Enter Search Query Here"
                InputProps={{
                  disableUnderline: true,
                }}
                onChange={this.onSearchQueryChange}
              />
            </div>
            <div className="Search-Wrapper">
              <Button
                variant="contained"
                color="primary"
                id="Search-Button"
                onClick={this.onSearchClick}
                disabled={loading}
              >
                <SearchIcon/> Search Code
              </Button>
            </div>
            {
              loading ?
                <LinearProgress color="primary" /> :
                <div className="Search-Results">
                  <h2 className="Search-Results-Title">Search Results</h2>
                  {
                    codeResults.map((attrs, index) => <CodeSample key={index} {...attrs}/>)
                  }
                </div>
            }
        </div>
      </MuiThemeProvider>
    );
  }

  onSearchQueryChange = (e) => {
    const {value} = e.target;
    this.setState({queryStr: value});
  };

  onSearchClick = () => {
    const {queryStr} = this.state;
    if (queryStr) {
      this.setState({loading: true});
      code_search_api(queryStr).then((res) => {
        this.setState({codeResults: res.body.result, loading: false});
      }).catch((err) => {
        console.log(err);
        this.setState({loading: false});
      });
    }
  };
}

export default App;
