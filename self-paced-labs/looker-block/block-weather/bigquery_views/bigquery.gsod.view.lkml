view: bq_gsod {
  sql_table_name: `cloud-training-demos.noaa_gsod.gsod*` ;;

  dimension: primary_key {
    hidden: yes
    primary_key: yes
    type: string
    sql: concat(cast(${station} as string), ${wban}, cast(${weather_date} as string)) ;;
  }

  dimension: station_id {
    group_label: "Station"
    label: "Station ID"
    type: string
    sql: CASE WHEN ${wban} = '99999' THEN ${station} ELSE ${wban} END;;
  }

  dimension: station {
    group_label: "Station"
    label: "Station"
    type: string
    sql: ${TABLE}.stn ;;
  }

  dimension: wban {
    group_label: "Station"
    label: "WBAN"
    hidden: yes
    type: string
    sql: ${TABLE}.wban ;;
  }

  dimension_group: weather {
    type: time
    timeframes: [date, month, month_name, year]
    sql: TIMESTAMP(concat(${year},'-',${month},'-',${day})) ;;
    convert_tz: no
  }

## Weather Events

  dimension: rainfall {
    group_label: "Weather Event"
    type: number
    sql: case when ${TABLE}.prcp = 99.99 then null else ${TABLE}.prcp end;;
  }

  dimension: snow {
    group_label: "Weather Event"
    label: "Snow (inches)"
    type: number
    sql: case when ${TABLE}.sndp = 999.9 then null else ${TABLE}.sndp end;;
  }

  dimension: windspeed {
    group_label: "Weather Event"
    type: string
    sql: ${TABLE}.wdsp ;;
  }

  dimension: dew_point {
    group_label: "Weather Event"
    type: number
    sql: case when ${TABLE}.dewp = 9999.9 then null else ${TABLE}.dewp end ;;
  }

  dimension: max_wind_speed {
    group_label: "Weather Event"
    type: string
    sql: case when ${TABLE}.mxpsd = 999.9 then null else ${TABLE}.mxpsd end ;;
  }

  dimension: gust {
    group_label: "Weather Event"
    type: number
    sql: ${TABLE}.gust ;;
  }

  dimension: visibility {
    group_label: "Weather Event"
    type: number
    sql: case when ${TABLE}.visib then null else ${TABLE}.visib end ;;
  }

  dimension: sea_level_pressure {
    group_label: "Weather Event"
    type: number
    sql: ${TABLE}.slp ;;
  }

  dimension: mean_station_pressure {
    group_label: "Weather Event"
    type: number
    sql: ${TABLE}.stp ;;
  }

  dimension: temperature {
    group_label: "Weather Event"
    type: number
    sql: case when ${TABLE}.temp = 9999.9 then null else ${TABLE}.temp end ;;
  }

  dimension: flag_prcp {
    hidden: yes
    type: string
    sql: ${TABLE}.flag_prcp ;;
  }

## Event Occurence

  dimension: has_rainfall {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${rainfall} > 0.0 ;;
  }

  dimension: has_snow {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${snow} > 0.0 ;;
  }

  dimension: has_fog {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${TABLE}.fog = '1';;
  }

  dimension: has_hail {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${TABLE}.hail = '1' ;;
  }

  dimension: has_rain_drizzle {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${TABLE}.rain_drizzle = '1' ;;
  }

  dimension: has_snow_ice_pellets {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${TABLE}.snow_ice_pellets = '1' ;;
  }

  dimension: has_thunder {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${TABLE}.thunder = '1';;
  }

  dimension: has_tornado_funnel_cloud {
    group_label: "Event Occurrence"
    type: yesno
    sql: ${TABLE}.tornado_funnel_cloud = '1' ;;
  }


## Row Measures

  measure: total_rainfall {
    group_label: "Station"
    type: sum
    sql: ${rainfall} ;;
    value_format_name: decimal_2
  }

  measure: total_snow_inches {
    group_label: "Station"
    type: sum
    sql: ${snow};;
    value_format_name: decimal_2
  }

  measure: average_rainfall {
    type: average
    sql: ${rainfall} ;;
    value_format_name: decimal_2
  }

  measure: average_temperature {
    type: average
    sql: ${temperature} ;;
    value_format_name: decimal_2
  }

  measure: min_temperature {
    type: min
    sql: ${temperature} ;;
    value_format_name: decimal_2
  }

  measure: percentile_25_temperature {
    type: percentile
    percentile: 25
    sql: ${temperature} ;;
  }

  measure: median_temperature {
    type: median
    sql: ${temperature} ;;
  }

  measure: percentile_75_temperature {
    type: percentile
    percentile: 75
    sql: ${temperature} ;;
  }

  measure: max_temperature {
    type: max
    sql: ${temperature} ;;
    value_format_name: decimal_2
  }

## Daily Measures (Count of Days w/ X Event) --

  measure: total_days_with_fog {
    group_label: "Daily Facts"
    type: number
    sql: count(distinct case when ${has_fog} = true then ${weather_date} else null end) ;;
  }

  measure: total_days_with_rainfall {
    group_label: "Daily Facts"
    type: number
    sql: count(distinct case when ${has_rainfall} = true then ${weather_date} else null end) ;;
  }

  measure: total_days_with_hail {
    group_label: "Daily Facts"
    type: number
    sql: count(distinct case when ${has_hail} = true then ${weather_date} else null end) ;;
  }

  measure: total_days_with_thunder {
    group_label: "Daily Facts"
    type: number
    sql: count(distinct case when ${has_thunder} = true then ${weather_date} else null end) ;;
  }

  measure: total_days_with_tornado {
    group_label: "Daily Facts"
    type: number
    sql: count(distinct case when ${has_tornado_funnel_cloud} = true then ${weather_date} else null end) ;;
  }

  measure: total_days_with_snow {
    group_label: "Daily Facts"
    type: number
    sql: count(distinct case when ${has_snow} = true then ${weather_date} else null end) ;;
  }


  ## Unused Fields

  measure: count {
    hidden: no
    type: count
    label: "Event Count"
  }

  dimension: year {
    hidden: yes
    type: string
    sql: REGEXP_EXTRACT(_TABLE_SUFFIX,r'\d\d\d\d') ;;
  }

  dimension: month {
    hidden: yes
    type: string
    sql: ${TABLE}.mo ;;
  }

  dimension: day {
    hidden: yes
    type: string
    sql: ${TABLE}.da ;;
  }

  dimension: count_dewp {
    hidden: yes
    type: number
    sql: ${TABLE}.count_dewp ;;
  }

  dimension: count_slp {
    hidden: yes
    type: number
    sql: ${TABLE}.count_slp ;;
  }

  dimension: count_stp {
    hidden: yes
    type: number
    sql: ${TABLE}.count_stp ;;
  }

  dimension: count_temp {
    hidden: yes
    type: number
    sql: ${TABLE}.count_temp ;;
  }

  dimension: flag_max_temp {
    hidden: yes
    type: string
    sql: ${TABLE}.flag_max ;;
  }

  dimension: flag_min_temp {
    hidden: yes
    type: string
    sql: ${TABLE}.flag_min ;;
  }

  dimension: count_visib {
    hidden: yes
    type: number
    sql: ${TABLE}.count_visib ;;
  }

  dimension: count_wdsp {
    hidden: yes
    type: string
    sql: ${TABLE}.count_wdsp ;;
  }
}
