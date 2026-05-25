import { useEffect, useMemo, useState } from 'react';
import { BeyPanel } from './components/BeyPanel';
import { fetchParts } from './services/partsApi';
import { BeySelection, PART_LABELS, PART_ORDER, PartsResponse, PartType } from './types/parts';

// --- buildInitialSelection ------------------------------------------------------
//【呼ばれる場面】API取得後に左右フォームの初期値を確定するときに呼ばれる。
//【すること】各パーツ種別の先頭候補を採用して全キーを埋め、未選択キーがない安定した初期選択状態を生成する。
//【入力】partsData（サーバー取得済みのパーツ全体定義（PartsResponse））
//【出力】全パーツ初期選択値（BeySelection）
//【外部境界】なし
// -------------------------------------------------------------------------------
function buildInitialSelection(partsData: PartsResponse): BeySelection {
  const selection = {} as BeySelection;
  PART_ORDER.forEach((partType) => {
    selection[partType] = partsData.parts[partType][0]?.name ?? '';
  });
  return selection;
}

// --- buildSummary ---------------------------------------------------------------
//【呼ばれる場面】左右パネル下に現在選択の要約を表示するため、レンダリング時に呼ばれる。
//【すること】固定順のパーツラベルと選択値を結合し、片側構成を一行で確認できる表示文字列へ整形する。
//【入力】selection（片側の選択状態（BeySelection））
//【出力】サマリー文字列（string）
//【外部境界】なし
// -------------------------------------------------------------------------------
function buildSummary(selection: BeySelection): string {
  return PART_ORDER.map((partType) => `${PART_LABELS[partType]}: ${selection[partType]}`).join(' / ');
}

// --- App -----------------------------------------------------------------------
//【呼ばれる場面】Reactアプリのルート描画時に呼ばれる。
//【すること】初回にJava REST APIからパーツを取得し、左右独立フォームの状態を管理して選択結果を同時表示する。
//【入力】なし
//【出力】アプリ全体UI（JSX.Element）
//【外部境界】React state（useState）, React effect（useEffect）, HTTP通信（fetchParts）
// -------------------------------------------------------------------------------
export default function App(): JSX.Element {
  const [partsData, setPartsData] = useState<PartsResponse | null>(null);
  const [leftSelection, setLeftSelection] = useState<BeySelection | null>(null);
  const [rightSelection, setRightSelection] = useState<BeySelection | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    fetchParts()
      .then((loaded) => {
        if (!isMounted) return;
        const initial = buildInitialSelection(loaded);
        setPartsData(loaded);
        setLeftSelection(initial);
        setRightSelection(initial);
      })
      .catch((error: unknown) => {
        if (!isMounted) return;
        setErrorMessage(error instanceof Error ? error.message : '不明なエラーが発生しました。');
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handleLeftChange = (partType: PartType, value: string): void => {
    setLeftSelection((previous) => (previous ? { ...previous, [partType]: value } : previous));
  };

  const handleRightChange = (partType: PartType, value: string): void => {
    setRightSelection((previous) => (previous ? { ...previous, [partType]: value } : previous));
  };

  const leftSummary = useMemo(() => (leftSelection ? buildSummary(leftSelection) : ''), [leftSelection]);
  const rightSummary = useMemo(() => (rightSelection ? buildSummary(rightSelection) : ''), [rightSelection]);

  if (errorMessage) {
    return <p>読み込みエラー: {errorMessage}</p>;
  }

  if (!partsData || !leftSelection || !rightSelection) {
    return <p>パーツデータを読み込み中です...</p>;
  }

  return (
    <main style={{ maxWidth: 1200, margin: '0 auto', padding: 24, fontFamily: 'sans-serif' }}>
      <h1>ベイ使用登録フォーム（左右独立）</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <BeyPanel title="左" selection={leftSelection} onPartChange={handleLeftChange} partsData={partsData} />
        <BeyPanel title="右" selection={rightSelection} onPartChange={handleRightChange} partsData={partsData} />
      </div>
      <section style={{ marginTop: 16 }}>
        <h2>現在の選択</h2>
        <p>左: {leftSummary}</p>
        <p>右: {rightSummary}</p>
      </section>
    </main>
  );
}
