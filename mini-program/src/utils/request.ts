export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

/** 将后端返回的文件 URL 转成小程序当前环境可访问的地址（避免 127.0.0.1 等内网 host 导致预览黑屏） */
export const resolveFileUrl = (fileUrl: string): string => {
  if (!fileUrl) return fileUrl;
  if (!/^https?:\/\//i.test(fileUrl)) return fileUrl;
  try {
    const apiOrigin = new URL(BASE_URL).origin;
    const parsed = new URL(fileUrl);
    return `${apiOrigin}${parsed.pathname}${parsed.search}`;
  } catch {
    return fileUrl;
  }
};

const LOGIN_URLS = ["/login", "/login/wx", "/login/wx/agency"];

const isLoginUrl = (url: string) => LOGIN_URLS.some((p) => url.startsWith(p));

export const request = <T = any>(
  url: string,
  method: "GET" | "POST" | "PUT" | "DELETE" = "GET",
  data?: any,
  header?: any,
): Promise<T> => {
  return new Promise((resolve, reject) => {
    const token = isLoginUrl(url) ? "" : uni.getStorageSync("token");
    uni.request({
      url: BASE_URL + url,
      method,
      data,
      header: {
        "content-type": "application/json",
        "x-access-token": token || "",
        ...header,
      },
      success: (res: any) => {
        const { code, data, msg } = res.data || {};
        if (code === 200) {
          resolve(data);
        } else if (code === 401) {
          const isLoginRequest = isLoginUrl(url);
          uni.showToast({
            title: isLoginRequest ? msg || "登录失败" : "登录过期，请重新登录",
            icon: "none",
          });
          if (!isLoginRequest) {
            uni.removeStorageSync("token");
            uni.removeStorageSync("userInfo");
            uni.reLaunch({ url: "/pages/patient/home" });
          }
          reject(new Error(msg || "登录过期"));
        } else {
          uni.showToast({ title: msg || "请求失败", icon: "none" });
          reject(new Error(msg || "请求失败"));
        }
      },
      fail: (err) => {
        uni.showToast({ title: "网络异常，请稍后重试", icon: "none" });
        reject(err);
      },
    });
  });
};
