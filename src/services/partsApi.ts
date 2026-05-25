import apiConfig from '../config/apiConfig.json';
import { PartsResponse } from '../types/parts';

// --- fetchParts ----------------------------------------------------------------
//【呼ばれる場面】フォーム描画前にパーツ候補をロードするため、初回表示時に呼ばれる。
//【すること】Python GUIが管理するAPI設定URLへHTTP GETを実行し、失敗時は詳細付きで例外化して呼び出し元がエラー表示へ分岐できるようにする。
//【入力】なし
//【出力】パーツ一覧JSON（Promise<PartsResponse>）
//【外部境界】HTTP通信（fetch）、設定JSON参照（apiConfig.json）
// -------------------------------------------------------------------------------
export async function fetchParts(): Promise<PartsResponse> {
  const response = await fetch(apiConfig.partsApiUrl);
  if (!response.ok) {
    throw new Error(`パーツ取得に失敗しました: ${response.status}`);
  }
  return (await response.json()) as PartsResponse;
}
