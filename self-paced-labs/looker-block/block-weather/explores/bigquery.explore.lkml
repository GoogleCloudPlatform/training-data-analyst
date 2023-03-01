include: "/bigquery_views/bigquery.*.view.lkml"

explore: gsod {
  from: bq_gsod
  join: zipcode_station {
    from: bq_zipcode_station
    view_label: "Geography"
    type: left_outer
    relationship: many_to_one
    sql_on: ${gsod.station_id} = ${zipcode_station.nearest_station_id}
      and ${gsod.year} = ${zipcode_station.year};;
  }
  join: stations {
    from: bq_stations
    type: left_outer
    relationship: many_to_one
    sql_on: ${gsod.station_id} = ${stations.station_id} ;;
  }
  join: zipcode_county{
    from: bq_zipcode_county
    view_label: "Geography"
    type: left_outer
    relationship: many_to_one
    sql_on: ${zipcode_station.zipcode} = ${zipcode_county.zipcode}  ;;
  }
  join: zipcode_facts {
    from: bq_zipcode_facts
    view_label: "Geography"
    type: left_outer
    relationship: one_to_many
    sql_on: ${zipcode_county.zipcode} = ${zipcode_facts.zipcode} ;;
  }
}

explore: zipcode_county {
  from: bq_zipcode_county
  join: zipcode_facts {
    from: bq_zipcode_facts
    type: left_outer
    sql_on: ${zipcode_county.zipcode} = ${zipcode_facts.zipcode} ;;
    relationship: one_to_many
  }
  join: zipcode_station {
    from: bq_zipcode_station
    type: left_outer
    relationship: many_to_one
    sql_on: ${zipcode_county.zipcode} = ${zipcode_station.zipcode} ;;
  }
  join: stations {
    from: bq_stations
    type: left_outer
    relationship: one_to_one
    sql_on: ${zipcode_station.nearest_station_id} = ${stations.station_id} ;;
  }
}
