export const BASE_URL = "http://101.43.141.29:8085/api";

export const request = <T = any>(
  url: string,
  method: "GET" | "POST" | "PUT" | "DELETE" = "GET",
  data?: any,
  header?: any,
): Promise<T> => {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync("token");
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
          uni.showToast({ title: "登录过期，请重新登录", icon: "none" });
          uni.removeStorageSync("token");
          uni.removeStorageSync("userInfo");
          uni.reLaunch({ url: "/pages/login/index" });
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
