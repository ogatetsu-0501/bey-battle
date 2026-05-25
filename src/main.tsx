import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// --- bootstrap -----------------------------------------------------------------
//【呼ばれる場面】ブラウザがmain.tsxを最初に読み込んだ直後に呼ばれる。
//【すること】root要素の存在を検証し、存在しない場合は即時に例外で停止し、存在する場合のみReactアプリをマウントする。
//【入力】なし
//【出力】なし（void）
//【外部境界】DOM（document.getElementById）、ReactDOM.createRoot
// -------------------------------------------------------------------------------
function bootstrap(): void {
  const rootElement = document.getElementById('root');

  // rootが無いと描画先が不定になり、アプリが起動不能になるため即停止する。
  if (!rootElement) {
    throw new Error('Root element (#root) was not found.');
  }

  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

bootstrap();
