/**
 * v-auth
 * 按钮权限指令
 */
import { useAuthStore } from "@/stores/modules/auth";
import type { Directive, DirectiveBinding } from "vue";

const auth: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding;
    const authStore = useAuthStore();
    const currentPageRoles = authStore.authButtonListGet[authStore.routeName] ?? [];
    const globalCodes = authStore.authButtonCodesGet ?? [];

    const hasCode = (code: string) => currentPageRoles.includes(code) || globalCodes.includes(code);

    if (value instanceof Array && value.length) {
      const hasPermission = value.every(item => hasCode(item));
      if (!hasPermission) el.remove();
    } else {
      if (!hasCode(value)) el.remove();
    }
  }
};

export default auth;
