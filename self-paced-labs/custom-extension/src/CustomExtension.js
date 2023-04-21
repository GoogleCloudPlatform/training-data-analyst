import React, { useEffect, useState, useContext, createRef } from 'react'
import { Space, ComponentsProvider, Text, FieldSelect, Button, theme } from '@looker/components'
import { ExtensionContext40 } from '@looker/extension-sdk-react'
import { LookerEmbedSDK } from '@looker/embed-sdk'
import styled from 'styled-components'


// Some styled components for look and feel
export const DemoContainer = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  gap: 1rem;
  padding: 3rem;
  width: 100vw;
  height: 100vh;
//  border-color: ${({ theme }) => theme.colors.inverse};
//  background-color: ${({ theme }) => theme.colors.ui3};
`

export const FilterContainer = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  align-items: center;
  width: 100%;
//  border-color: ${({ theme }) => theme.colors.neutralAccent};
//  background-color: ${({ theme }) => theme.colors.text1};
`

export const EmbedContainer = styled.div`
  width: 100%;
  height: 95vh;
  & > iframe {
    width: 100%;
    height: 100%;
  }
`

//ID of the dashboard to embed
const DASH_ID = 91
// Name of the dashboard filter to update
const DASH_FILTER = 'Country Name'
// Request to Looker API to fetch filter values (see Looker API documentation for 'run_inline_query')
const FILTER_REQUEST = {
  model: 'covid-extension',
  view: 'covid_test_explore',
  fields: ['covid_test_explore.country_name'], //Make sure we only put one field in this array
  limit: 100
}

// Fetch filter values with the Looker API
// Render in a Looker component https://looker-open-source.github.io/components/latest/
const DashboardFilters = ({updateFilters}) => {
  const { coreSDK } = useContext(ExtensionContext40)
  const [filters, setFilters] = useState([])
  const [choice, setChoice] = useState('')

  useEffect(() => {
    const initialize = async () => {
      let r = await coreSDK.ok(coreSDK.run_inline_query({
        result_format: 'json',
        body: FILTER_REQUEST
      }))
      setFilters(r)
    }
    initialize()
  }, [])

  const selectFilter = (value) => {
    setChoice(value)
    updateFilters(value)
  }

  return (
    <FilterContainer>
      <FieldSelect
        name="Dashboard Filter"
        label="Dashboard Filter"
        placeholder={filters.length == 0 ? 'Loading...' : 'Choose a value'}
        value={choice}
        options={filters.map(f => ({value: String(f[FILTER_REQUEST.fields[0]])}))} // transform to the right format
        disabled={filters.length == 0}
        onChange={selectFilter}
      />
    </FilterContainer>
  )
}

export const QwiklabsDemo = () => {
  const { extensionSDK } = useContext(ExtensionContext40)
  const [dashboard, setDashboard] = useState()

  const embedCtrRef = createRef()

  useEffect(() => {
    const hostUrl = extensionSDK.lookerHostData.hostUrl
    LookerEmbedSDK.init(hostUrl)
    const initialize = async () => {
      try {
        LookerEmbedSDK.createDashboardWithId(DASH_ID)
        .appendTo(embedCtrRef.current)
        .build()
        .connect()
        .then(d => setDashboard(d))

      } catch (error) {
        console.error(error)
      }
    }
    initialize()
    return () => embedCtrRef.current.innerHTML = '';
  }, [])

  const updateFilters = (value) => {
    const newFilter = {}
    newFilter[DASH_FILTER] = value
    dashboard.updateFilters(newFilter)
    dashboard.run()
  }

  const message = 'Covid Dashboard - Executive View'
  return (
    <>
      <ComponentsProvider>
        <Space p="xxxxxlarge" width="100%" height="10vh" around>
          <Text p="xxxxxlarge" fontSize="xxxxxlarge">
            {message}
          </Text>
        </Space>

        <DemoContainer>
          <DashboardFilters updateFilters={updateFilters}/>
          <EmbedContainer ref={embedCtrRef} />
        </DemoContainer>
      </ComponentsProvider>
    </>
  )
}
