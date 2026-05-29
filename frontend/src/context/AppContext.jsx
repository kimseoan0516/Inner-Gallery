import { createContext, useContext, useState } from 'react'

const Ctx = createContext(null)

export function AppProvider({ children }) {
  const [result,        setResult]        = useState(null)
  const [selectedEntry, setSelectedEntry] = useState(null)
  const [preEmotion,    setPreEmotion]    = useState([])

  return (
    <Ctx.Provider value={{ result, setResult, selectedEntry, setSelectedEntry, preEmotion, setPreEmotion }}>
      {children}
    </Ctx.Provider>
  )
}

export const useApp = () => useContext(Ctx)
