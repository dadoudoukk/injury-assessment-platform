import { computed, ref } from 'vue'
import { DICT_CODES, useDictStore } from '@/store/modules/dict'
import type { DictOption } from '@/types/dict'

/** 案件相关字典：事故类型、伤情类型 */
export function useCaseDict() {
  const dictStore = useDictStore()
  const loading = ref(false)

  const accidentTypeOptions = computed<DictOption[]>(
    () => dictStore.getOptions(DICT_CODES.ACCIDENT_TYPE),
  )
  const injuryTypeOptions = computed<DictOption[]>(
    () => dictStore.getOptions(DICT_CODES.INJURY_TYPE),
  )

  async function loadDicts(force = false) {
    loading.value = true
    try {
      await dictStore.loadCaseDicts(force)
    } finally {
      loading.value = false
    }
  }

  function getAccidentTypeLabel(value: string) {
    return dictStore.getDictLabel(DICT_CODES.ACCIDENT_TYPE, value)
  }

  function getInjuryTypeLabel(value: string) {
    return dictStore.getDictLabel(DICT_CODES.INJURY_TYPE, value)
  }

  return {
    loading,
    accidentTypeOptions,
    injuryTypeOptions,
    loadDicts,
    getAccidentTypeLabel,
    getInjuryTypeLabel,
  }
}
