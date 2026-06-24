/** 页面路由路径统一管理 */
export const ROUTES = {
  PATIENT_HOME: '/pages/patient/home',
  PATIENT_LIST: '/pages/patient/list',
  PATIENT_CREATE: '/pages/patient/create',
  PATIENT_APPLICATION_DETAIL: '/pages/patient/application-detail',
  PATIENT_RESUBMIT: '/pages/patient/resubmit',
  AGENCY_LOGIN: '/pages/login/index',
  AGENCY_REGISTER: '/pages/agency/register',
  WORKBENCH: '/pages/index/index',
  MINE: '/pages/mine/index',
  DETAIL: '/pages/detail/index',
  SET_PASSWORD: '/pages/login/set-password',
  CHANGE_PASSWORD: '/pages/login/change-password',
} as const

/** 机构端相关路由前缀，用于 401 路由兜底推断 */
export const AGENCY_ROUTE_PREFIXES = [
  'pages/index/index',
  'pages/login/',
  'pages/mine/index',
  'pages/detail/index',
] as const
