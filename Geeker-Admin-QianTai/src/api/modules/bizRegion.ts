import { PORT1 } from "@/api/config/servicePort";
import http from "@/api";
import { ResPage } from "@/api/interface";

export interface RegionConfigRow {
  id: string;
  province: string;
  city: string;
  district: string;
  regionText: string;
  enabled: number;
  sort: number;
  remark?: string;
  createdAt: string;
  updatedAt: string;
}

export interface RegionConfigListParams {
  pageNum: number;
  pageSize: number;
  province?: string;
  enabled?: number;
}

export interface RegionConfigForm {
  province: string;
  city: string;
  district: string;
  enabled: number;
  sort: number;
  remark?: string;
}

export interface RegionConfigEditForm {
  enabled?: number;
  sort?: number;
  remark?: string;
}

export const getRegionConfigList = (params: RegionConfigListParams) => {
  return http.get<ResPage<RegionConfigRow>>(PORT1 + `/biz/region`, params);
};

export const addRegionConfig = (params: RegionConfigForm) => {
  return http.post(PORT1 + `/biz/region`, params);
};

export const editRegionConfig = (id: string, params: RegionConfigEditForm) => {
  return http.put(PORT1 + `/biz/region/${id}`, params);
};

export const deleteRegionConfig = (id: string) => {
  return http.delete(PORT1 + `/biz/region/${id}`);
};
