import { defineStore } from "pinia";
import { AuthState } from "@/stores/interface";
import { getAuthButtonCodesApi, getAuthButtonListApi, getAuthMenuListApi } from "@/api/modules/login";
import { getFlatMenuList, getShowMenuList, getAllBreadcrumbList } from "@/utils";

export const useAuthStore = defineStore({
  id: "geeker-auth",
  state: (): AuthState => ({
    authButtonList: {},
    authButtonCodes: [],
    authMenuList: [],
    routeName: ""
  }),
  getters: {
    authButtonListGet: state => state.authButtonList,
    authButtonCodesGet: state => state.authButtonCodes,
    authMenuListGet: state => state.authMenuList,
    showMenuListGet: state => getShowMenuList(state.authMenuList),
    flatMenuListGet: state => getFlatMenuList(state.authMenuList),
    breadcrumbListGet: state => getAllBreadcrumbList(state.authMenuList)
  },
  actions: {
    async getAuthButtonList() {
      const [buttonsRes, codesRes] = await Promise.all([getAuthButtonListApi(), getAuthButtonCodesApi()]);
      this.authButtonList = buttonsRes.data;
      this.authButtonCodes = codesRes.data || [];
    },
    // Get AuthMenuList
    async getAuthMenuList() {
      const { data } = await getAuthMenuListApi();
      this.authMenuList = data;
    },
    // Set RouteName
    async setRouteName(name: string) {
      this.routeName = name;
    }
  }
});
