export const PART_ORDER = [
  'productLine',
  'lockChip',
  'blade',
  'metalBlade',
  'mainBlade',
  'assistBlade',
  'overBlade',
  'ratchet',
  'bit'
] as const;

export type PartType = (typeof PART_ORDER)[number];

export type PartOption = {
  name: string;
  requiredParts: PartType[];
};

export type PartsResponse = {
  partTypes: PartType[];
  parts: Record<PartType, PartOption[]>;
};

export type BeySelection = Record<PartType, string>;

export const PART_LABELS: Record<PartType, string> = {
  productLine: '製品ライン',
  lockChip: 'ロックチップ',
  blade: 'ブレード',
  metalBlade: 'メタルブレード',
  mainBlade: 'メインブレード',
  assistBlade: 'アシストブレード',
  overBlade: 'オーバーブレード',
  ratchet: 'ラチェット',
  bit: 'ビット'
};
