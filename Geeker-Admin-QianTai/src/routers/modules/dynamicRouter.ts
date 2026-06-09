import router from "@/routers/index";
import { LOGIN_URL } from "@/config";
import { RouteRecordRaw } from "vue-router";
import { ElNotification } from "element-plus";
import { useUserStore } from "@/stores/modules/user";
import { useAuthStore } from "@/stores/modules/auth";
import { useGlobalStore } from "@/stores/modules/global";
import { getUserInfoApi } from "@/api/modules/login";

// 引入 views 文件夹下所有 vue 文件
const modules = import.meta.glob("@/views/**/*.vue");

/** 将菜单 component 路径解析为懒加载组件 */
const resolveViewComponent = (componentPath: string) => {
  const normalized = componentPath.startsWith("/") ? componentPath : `/${componentPath}`;
  const candidates = [`/src/views${normalized}.vue`, `@/views${normalized}.vue`];

  for (const key of candidates) {
    if (modules[key]) return modules[key];
  }

  const suffix = `${normalized}.vue`.replace(/\\/g, "/");
  const matchedKey = Object.keys(modules).find(key => key.replace(/\\/g, "/").endsWith(suffix));
  return matchedKey ? modules[matchedKey] : undefined;
};

/**
 * @description 初始化动态路由
 */
export const initDynamicRouter = async () => {
  const userStore = useUserStore();
  const authStore = useAuthStore();
  const globalStore = useGlobalStore();

  try {
    // 1.获取当前用户信息
    const infoRes = await getUserInfoApi();
    userStore.setUserInfo({
      name: infoRes.data?.name || "管理员",
      roleName: infoRes.data?.roleName || infoRes.data?.roles?.[0] || "管理员",
      agencyId: infoRes.data?.agencyId ?? null
    });

    await globalStore.initSysConfig();

    // 2.获取菜单列表 && 按钮权限列表
    await authStore.getAuthMenuList();
    await authStore.getAuthButtonList();

    // 3.判断当前用户有没有菜单权限
    if (!authStore.authMenuListGet.length) {
      ElNotification({
        title: "无权限访问",
        message: "当前账号无任何菜单权限，请联系系统管理员！",
        type: "warning",
        duration: 3000
      });
      userStore.setToken("");
      router.replace(LOGIN_URL);
      return Promise.reject("No permission");
    }

    // 4.添加动态路由
    authStore.flatMenuListGet.forEach(item => {
      if (item.path && router.getRoutes().some(route => route.path === item.path)) return;

      item.children && delete item.children;
      if (item.component && typeof item.component == "string") {
        const viewComponent = resolveViewComponent(item.component);
        if (!viewComponent) {
          console.warn(`[Vue Router] 未找到组件: ${item.component}，路由 ${item.path} 将跳过注册`);
          return;
        }
        item.component = viewComponent;
      } else if (!item.children?.length) {
        console.warn(`[Vue Router] 路由 ${item.path} 缺少 component，已跳过注册`);
        return;
      }
      if (item.meta.isFull) {
        router.addRoute(item as unknown as RouteRecordRaw);
      } else {
        router.addRoute("layout", item as unknown as RouteRecordRaw);
      }
    });
  } catch (error) {
    // 当按钮 || 菜单请求出错时，重定向到登陆页
    userStore.setToken("");
    router.replace(LOGIN_URL);
    return Promise.reject(error);
  }
};
