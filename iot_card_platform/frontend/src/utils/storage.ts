/**
 * 本地存储工具
 */

const PREFIX = 'iot_card_'

export const storage = {
  /**
   * 设置存储
   */
  set(key: string, value: any): void {
    try {
      const data = JSON.stringify(value)
      localStorage.setItem(PREFIX + key, data)
    } catch (error) {
      console.error('Storage set error:', error)
    }
  },

  /**
   * 获取存储
   */
  get<T = any>(key: string): T | null {
    try {
      const data = localStorage.getItem(PREFIX + key)
      if (!data) return null
      return JSON.parse(data) as T
    } catch (error) {
      console.error('Storage get error:', error)
      return null
    }
  },

  /**
   * 移除存储
   */
  remove(key: string): void {
    try {
      localStorage.removeItem(PREFIX + key)
    } catch (error) {
      console.error('Storage remove error:', error)
    }
  },

  /**
   * 清空所有存储
   */
  clear(): void {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith(PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Storage clear error:', error)
    }
  }
}

export const sessionStorage = {
  /**
   * 设置会话存储
   */
  set(key: string, value: any): void {
    try {
      const data = JSON.stringify(value)
      window.sessionStorage.setItem(PREFIX + key, data)
    } catch (error) {
      console.error('SessionStorage set error:', error)
    }
  },

  /**
   * 获取会话存储
   */
  get<T = any>(key: string): T | null {
    try {
      const data = window.sessionStorage.getItem(PREFIX + key)
      if (!data) return null
      return JSON.parse(data) as T
    } catch (error) {
      console.error('SessionStorage get error:', error)
      return null
    }
  },

  /**
   * 移除会话存储
   */
  remove(key: string): void {
    try {
      window.sessionStorage.removeItem(PREFIX + key)
    } catch (error) {
      console.error('SessionStorage remove error:', error)
    }
  },

  /**
   * 清空所有会话存储
   */
  clear(): void {
    try {
      const keys = Object.keys(window.sessionStorage)
      keys.forEach(key => {
        if (key.startsWith(PREFIX)) {
          window.sessionStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('SessionStorage clear error:', error)
    }
  }
}
