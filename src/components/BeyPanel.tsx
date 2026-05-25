import { BeySelection, PART_LABELS, PART_ORDER, PartType, PartsResponse } from '../types/parts';

type BeyPanelProps = {
  title: string;
  selection: BeySelection;
  onPartChange: (partType: PartType, value: string) => void;
  partsData: PartsResponse;
};

// --- buildRequirementText -------------------------------------------------------
//【呼ばれる場面】各プルダウンの補助表示で、選択肢の必須パーツ情報を人間可読に変換するときに呼ばれる。
//【すること】requiredPartsが空なら「制約なし」を返し、存在する場合は日本語ラベルへ変換して区切り文字で連結する。
//【入力】requiredParts（候補が要求する他パーツ種別一覧（PartType[]））
//【出力】UI表示用の制約テキスト（string）
//【外部境界】なし
// -------------------------------------------------------------------------------
function buildRequirementText(requiredParts: PartType[]): string {
  if (requiredParts.length === 0) {
    return '制約なし';
  }
  return requiredParts.map((partType) => PART_LABELS[partType]).join(' / ');
}

// --- BeyPanel ------------------------------------------------------------------
//【呼ばれる場面】左右それぞれの構成入力領域を描画するときに呼ばれる。
//【すること】全パーツ種別に対してプルダウンを生成し、選択変更を親へ通知して独立した片側構成を維持する。
//【入力】title（表示タイトル（string））, selection（現在の選択状態（BeySelection））, onPartChange（変更通知関数）, partsData（API取得済みパーツ一覧）
//【出力】片側入力パネルのUI（JSX.Element）
//【外部境界】なし
// -------------------------------------------------------------------------------
export function BeyPanel({ title, selection, onPartChange, partsData }: BeyPanelProps): JSX.Element {
  return (
    <section style={{ border: '1px solid #ccc', borderRadius: 8, padding: 16 }}>
      <h2>{title}</h2>
      {PART_ORDER.map((partType) => {
        const options = partsData.parts[partType];
        return (
          <div key={partType} style={{ marginBottom: 12, display: 'grid', gap: 6 }}>
            <label htmlFor={`${title}-${partType}`}>{PART_LABELS[partType]}</label>
            <select
              id={`${title}-${partType}`}
              value={selection[partType]}
              onChange={(event) => onPartChange(partType, event.target.value)}
            >
              {options.map((option) => (
                <option key={option.name} value={option.name}>
                  {option.name}
                </option>
              ))}
            </select>
            <small>
              必須: {buildRequirementText(options.find((option) => option.name === selection[partType])?.requiredParts ?? [])}
            </small>
          </div>
        );
      })}
    </section>
  );
}
