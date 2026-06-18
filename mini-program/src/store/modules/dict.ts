import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchDictByCode } from '@/api/dict'
import type { DictOption } from '@/types/dict'

export const DICT_CODES = {
  ACCIDENT_TYPE: 'biz_accident_type',
  INJURY_TYPE: 'biz_injury_type',
} as const

export type DictCode = (typeof DICT_CODES)[keyof typeof DICT_CODES]

export const useDictStore = defineStore('dict', () => {
  const cache = ref<Record<string, DictOption[]>>({})
  /** 进行中的请求，并发调用方复用同一 promise */
  const inflight = new Map<string, Promise<DictOption[]>>()

  async function loadDict(dictCode: string, force = false): Promise<DictOption[]> {
    if (!force && cache.value[dictCode]?.length) {
      return cache.value[dictCode]
    }

    const pending = inflight.get(dictCode)
    if (pending && !force) {
      return pending
    }

    const request = (async () => {
      try {
        const data = await fetchDictByCode(dictCode)
        cache.value[dictCode] = data || []
        return cache.value[dictCode]
      } catch (error) {
        console.error(`Load dict ${dictCode} error:`, error)
        return cache.value[dictCode] || []
      } finally {
        inflight.delete(dictCode)
      }
    })()

    inflight.set(dictCode, request)
    return request
  }

  async function loadAccidentTypes(force = false) {
    return loadDict(DICT_CODES.ACCIDENT_TYPE, force)
  }

  async function loadInjuryTypes(force = false) {
    return loadDict(DICT_CODES.INJURY_TYPE, force)
  }

  async function loadCaseDicts(force = false) {
    const [accidentTypes, injuryTypes] = await Promise.all([
      loadAccidentTypes(force),
      loadInjuryTypes(force),
    ])
    return { accidentTypes, injuryTypes }
  }

  function getOptions(dictCode: string): DictOption[] {
    return cache.value[dictCode] || []
  }

  function getDictLabel(dictCode: string, value: string): string {
    const options = getOptions(dictCode)
    return options.find((item) => item.dictValue === value)?.dictLabel || value
  }

  function clearCache(dictCode?: string) {
    if (dictCode) {
      delete cache.value[dictCode]
      inflight.delete(dictCode)
      return
    }
    cache.value = {}
    inflight.clear()
  }

  return {
    cache,
    loadDict,
    loadAccidentTypes,
    loadInjuryTypes,
    loadCaseDicts,
    getOptions,
    getDictLabel,
    clearCache,
  }
})
