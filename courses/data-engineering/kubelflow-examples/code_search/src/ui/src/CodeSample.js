import React, { Component } from 'react';
import PropTypes from 'prop-types';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/styles/hljs';
import CodeIcon from '@material-ui/icons/Code';

class CodeSample extends Component {
  render() {
    const {nwo, path, original_function, lineno} = this.props;

    const codeUrl = `${nwo}/blob/master/${path}#L${lineno}`;

    return (
      <div className="Code-Sample">
        <div className="Code-Url">
          <a
            href={`//github.com/${codeUrl}`}
            target="_blank"
            rel="nofollow noopener noreferrer"
          >
            <CodeIcon className="Code-Icon" />
          </a>
          <p><b>{nwo}/{path}#L{lineno}</b></p>
        </div>

        <SyntaxHighlighter style={docco}>
          {original_function}
        </SyntaxHighlighter>
      </div>
    );
  }
}

CodeSample.propTypes = {
  nwo: PropTypes.string.isRequired,
  path: PropTypes.string.isRequired,
  original_function: PropTypes.string.isRequired,
  lineno: PropTypes.string.isRequired,
};

export default CodeSample;
