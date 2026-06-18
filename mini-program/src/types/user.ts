export interface UserInfo {
  id?: string | number
  username?: string
  name?: string
  nickname?: string
  phone?: string
  avatar?: string
  roleName?: string
  agencyId?: string | number | null
  agencyName?: string
  contactPerson?: string
  contactPhone?: string
  province?: string
  city?: string
  district?: string
  address?: string
  mustChangePassword?: boolean
  [key: string]: unknown
}

export interface ChangePasswordBody {
  oldPassword: string
  newPassword: string
}

export interface SetInitialPasswordBody {
  newPassword: string
}
