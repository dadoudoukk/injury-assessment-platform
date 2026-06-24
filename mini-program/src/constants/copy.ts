/** 通用业务文案 */
export const APP_COPY = {
  brandTitle: '人伤鉴定共享中心',
  brandSubtitle: '让鉴定更透明 · 让理赔更高效',
  networkError: '网络异常，请稍后重试',
  requestFailed: '请求失败',
  sessionExpired: '登录过期，请重新登录',
  loginFailed: '登录失败',
} as const

/** 统一反馈文案 */
export const FEEDBACK_COPY = {
  loginSuccess: '登录成功',
  submitSuccess: '提交成功',
  acceptSuccess: '已确认受理',
  caseCreateSuccess: '报案成功！',
  caseSubmitAuditSuccess: '报案已提交，请等待平台审核',
  resubmitSuccess: '补件已提交，请等待平台审核',
  passwordSetSuccess: '设置成功',
  passwordChangeSuccess: '密码已更新，请重新登录',
  passwordChangeTitle: '修改成功',
  loadFailed: '加载失败，请稍后重试',
  retry: '重新加载',
  validationRequired: '请填写完整的必填项',
  logoutConfirm: '确定要退出登录吗？',
} as const

/** 列表加载文案 */
export const LIST_COPY = {
  loading: '加载中...',
  loadMore: '上拉加载更多',
  loadMoreFailed: '加载失败，点击重试',
  noMorePatient: '没有更多记录了',
  noMoreAgency: '没有更多数据了',
} as const

/** 密码相关页 */
export const PASSWORD_COPY = {
  changeTitle: '修改密码',
  changeSubtitle: '修改后请使用新密码登录',
  setTitle: '设置登录密码',
  setSubtitle: '首次登录须设置密码，设置后可使用「手机号 + 密码」登录机构端',
  oldPassword: '原密码',
  oldPasswordPlaceholder: '请输入原密码',
  newPassword: '新密码',
  newPasswordPlaceholder: '至少 6 位',
  confirmPassword: '确认密码',
  confirmPasswordPlaceholder: '再次输入新密码',
  changeSubmit: '确认修改',
  setSubmit: '确认设置',
  logoutLink: '退出登录',
  oldPasswordRequired: '请输入原密码',
  passwordMinLength: '密码至少 6 位',
  newPasswordMinLength: '新密码至少 6 位',
  passwordMismatch: '两次密码不一致',
  forbiddenPlaceholderPassword: '不能使用系统占位密码',
} as const

/** 空状态预设文案 */
export const EMPTY_STATE_COPY = {
  defaultTitle: '暂无数据',
  patientListTitle: '暂无报案记录',
  patientListDesc: '您还没有提交过报案，可点击下方按钮快速报案',
  patientListAction: '快速报案',
  applicationNotFoundTitle: '申请不存在',
  applicationNotFoundDesc: '该申请可能已被删除或您暂无查看权限',
  agencyListTitle: '暂无相关案件卷宗',
  agencyListDesc: '当前筛选条件下没有案件，可切换其他状态查看',
  loadErrorTitle: '加载失败',
  loadErrorDesc: '网络异常或服务器繁忙，请稍后重试',
  detailNotFoundTitle: '案件不存在',
  detailNotFoundDesc: '该案件可能已被删除或您暂无查看权限',
} as const

/** 门户首页 */
export const PORTAL_COPY = {
  serviceFlowTitle: '服务流程',
  steps: ['在线报案', '机构受理', '鉴定取证', '出具报告'],
  patientEntryTitle: '我是伤者',
  patientEntryDesc: '我要报案鉴定 / 查进度',
  agencyEntryTitle: '我是鉴定机构',
  agencyEntryDesc: '登录工作台接单处理',
  workbenchTitle: '我的工作台',
  workbenchDesc: '接单处理 / 查看卷宗',
  mineTitle: '个人中心',
  mineDesc: '账号信息 / 退出登录',
  registerHint: '还没有机构账号？',
  registerLink: '点击申请入驻',
  agencyWelcome: '欢迎回来',
  phoneAuthRequired: '需要授权手机号才能使用',
  agencyAccountHint: '该手机号为机构账号，请使用机构入口登录',
} as const

/** 机构登录页 */
export const LOGIN_COPY = {
  title: '机构账号登录',
  subtitle: '审核通过后，可使用入驻手机号微信登录；已设密码的同事可用账号密码登录',
  wxLogin: '微信授权登录',
  divider: '或使用微信登录',
  username: '账号',
  usernamePlaceholder: '请输入手机号/账号',
  password: '密码',
  passwordPlaceholder: '请输入密码',
  submit: '登 录',
  footer: '忘记密码？请使用下方微信授权登录后重设密码',
  phoneAuthRequired: '需要授权手机号才能登录',
} as const

/** 报案页 */
export const CASE_FORM_COPY = {
  title: '我要报案',
  subtitle: '请如实填写案件信息，我们将为您就近分派鉴定机构',
  partySection: '当事人信息',
  partyDesc: '请填写伤者本人信息，便于机构联系',
  accidentSection: '事故信息',
  accidentDesc: '请准确填写出险时间、地点及事故类型',
  insuranceSection: '保险信息',
  insuranceDesc: '请填写与保单一致的报案号及承保公司',
  materialSection: '案件材料',
  materialDesc: '请上传保单图片（必填）及事故认定书（选填）',
  policyLabel: '保单图片',
  policyHint: '至少 1 张，仅支持图片',
  accidentDecisionLabel: '事故认定书',
  accidentDecisionHint: '选填，仅支持图片',
  addImage: '添加图片',
  submit: '提交报案',
  submitHint: '提交后可在我的报案查看进度',
} as const

/** 伤者申请单（审核前） */
export const APPLICATION_COPY = {
  detailTitle: '报案申请详情',
  resubmitTitle: '补件再提交',
  resubmitSubtitle: '请根据驳回原因修改可编辑项，锚点信息不可更改',
  lockedSection: '不可修改信息',
  lockedDesc: '以下信息为业务锚点，驳回后不可在线修改',
  editableSection: '可修改信息',
  attachmentSection: '附件材料',
  attachmentDesc: '历史材料只读展示；本批次可按类别追加新材料',
  attachmentHistory: '历史材料',
  policyHistory: '历史保单',
  accidentHistory: '历史事故认定书',
  policyNew: '本次新增保单',
  accidentNew: '本次新增事故认定书',
  batchHistoryDesc: '按提交批次查看材料与审核结果',
  attachmentNew: '本批次新增',
  addAttachment: '添加附件',
  addPolicyImage: '添加保单图片',
  addAccidentImage: '添加事故认定书',
  resubmit: '提交补件',
  resubmitHint: '提交后将进入平台审核',
  pendingHint: '平台正在审核您的报案申请，请耐心等待。',
  rejectedHint: '申请已被驳回，请查看原因后补件提交。',
  approvedHint: '申请已通过审核，可查看关联案件进度。',
  viewCase: '查看案件进度',
  goResubmit: '去补件',
  rejectReason: '驳回原因',
} as const

/** 机构案件详情 */
export const AGENCY_DETAIL_COPY = {
  videoCameraOnlyHint: '仅支持现场拍摄上传',
  documentRejectHint: '请根据平台驳回原因重新提交完整文书包',
  reportPendingHint: '文书已提交，正在等待平台审核，请耐心等待。',
  agencySubmitHistory: '机构提交历史',
  batchDocumentNumber: '文书编号',
  batchCertificate: '电子证书',
} as const

/** 个人中心 */
export const MINE_COPY = {
  title: '个人中心',
  patientRole: '伤者用户',
  agencyRole: '鉴定机构',
  accountSection: '账号信息',
  agencySection: '机构信息',
  agencySectionDesc: '以下为机构备案信息，如有变更请联系平台管理员',
  phoneLabel: '绑定手机号',
  phoneEmpty: '未绑定手机号',
  contactPerson: '联系人',
  contactPhone: '联系电话',
  region: '省市区',
  address: '详细地址',
  emptyValue: '暂无',
  changePassword: '修改密码',
  logout: '退出登录',
  logoutConfirm: '确定要退出登录吗？',
} as const

/** 机构入驻 */
export const AGENCY_REGISTER_COPY = {
  title: '机构入驻申请',
  subtitle: '请填写真实的鉴定机构信息，审核通过后请使用入驻手机号在机构端微信登录',
  basicSection: '机构信息',
  basicDesc: '请填写机构全称及联系人信息，便于平台审核联系',
  addressSection: '机构地址',
  addressDesc: '请填写准确的办公地址，便于伤者与服务对接',
  submit: '提交申请',
  submitHint: '提交后请耐心等待平台审核',
  submitSuccessTitle: '提交成功',
  submitSuccessContent:
    '您的入驻申请已提交，请耐心等待平台审核。审核通过后，请返回首页点击「我是鉴定机构」并使用入驻手机号微信登录。',
  mapPick: '地图选择',
  locationAuthTitle: '需要位置权限',
  locationAuthContent: '请在设置中允许小程序使用位置信息，以便选择机构地址',
  locationGoSettings: '去设置',
  locationNotConfigured: '地图功能未配置，请联系管理员',
  locationFallback: '无法打开地图，请手动输入地址',
} as const
