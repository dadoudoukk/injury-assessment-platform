export interface RegionFields {
  province: string;
  city: string;
  district: string;
}

/** 省市区 cascader 数组 → 三个独立字段 */
export const encodeRegion = (region: string[]): RegionFields => ({
  province: region[0]?.trim() || "",
  city: region[1]?.trim() || "",
  district: region[2]?.trim() || ""
});

/** 三个独立字段 → cascader 回显数组 */
export const decodeRegion = (province?: string, city?: string, district?: string): string[] => {
  const arr: string[] = [];
  if (province?.trim()) arr.push(province.trim());
  if (city?.trim()) arr.push(city.trim());
  if (district?.trim()) arr.push(district.trim());
  return arr;
};

/** 拼接为展示用地区文本 */
export const formatRegionText = (province?: string, city?: string, district?: string): string => {
  return decodeRegion(province, city, district).join(" / ");
};

/** 表单校验：须选择完整省 / 市 / 区 */
export const validateRegion = (_rule: unknown, value: string[], callback: (error?: Error) => void) => {
  if (!value || value.length < 3) {
    callback(new Error("请选择完整的省 / 市 / 区"));
    return;
  }
  callback();
};
