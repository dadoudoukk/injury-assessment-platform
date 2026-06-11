import { useUserStore } from "@/store/modules/user";
import { isAgencyUser } from "./role";

/** 机构工作台页：校验登录、机构身份与是否已设密 */
export async function ensureAgencySession(fetchInfo = true): Promise<boolean> {
  const userStore = useUserStore();
  if (!userStore.token) {
    uni.reLaunch({ url: "/pages/login/index" });
    return false;
  }
  if (fetchInfo) {
    await userStore.fetchUserInfo();
  }
  if (!isAgencyUser(userStore.userInfo)) {
    uni.reLaunch({ url: "/pages/patient/home" });
    return false;
  }
  if (userStore.userInfo?.mustChangePassword) {
    uni.reLaunch({ url: "/pages/login/set-password" });
    return false;
  }
  return true;
}

/** 机构登录成功后统一跳转 */
export async function completeAgencyLogin(res: {
  access_token: string;
  mustChangePassword?: boolean;
}) {
  const userStore = useUserStore();
  userStore.setToken(res.access_token);
  await userStore.fetchUserInfo();

  if (!isAgencyUser(userStore.userInfo)) {
    userStore.logout();
    uni.showToast({ title: "该账号不是机构账号", icon: "none" });
    return;
  }

  const mustChange =
    res.mustChangePassword === true || userStore.userInfo?.mustChangePassword === true;
  if (mustChange) {
    uni.reLaunch({ url: "/pages/login/set-password" });
  } else {
    uni.reLaunch({ url: "/pages/index/index" });
  }
}
