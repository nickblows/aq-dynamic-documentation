<!-- GENERATED FILE — DO NOT EDIT.
     Source: /docs/integration-catalog.yaml
     Regenerate: python3 scripts/generate_diagrams.py -->

# AQIE System Context

_Generated 2026-09-15T13:13:57Z from `/docs/integration-catalog.yaml`._

Every AQIE service with a confirmed integration, grouped by domain, with the external and platform systems they depend on. Edge labels show the endpoints used.

Arrow meaning: solid = synchronous request, thick = scheduled batch, dotted = asynchronous or user-redirect.

```mermaid
graph LR
  subgraph Citizen_domain["Citizen domain"]
    aqie_dataselector_frontend["dataselector-frontend"]
    aqie_dc_admin_frontend["dc-admin-frontend"]
    aqie_dc_frontend["dc-frontend"]
    aqie_demo_data_visualisations["demo-data-visualisations"]
    aqie_docanalysisawspoc_frontend["docanalysisawspoc-frontend"]
    aqie_docanalysispoc_frontend["docanalysispoc-frontend"]
    aqie_front_end["front-end"]
    aqie_laqm_data_explorer["laqm-data-explorer"]
    aqie_maps_frontend["maps-frontend"]
    aqie_maps_prototype["maps-prototype"]
    aqie_prtr_frontend["prtr-frontend"]
  end
  subgraph Data_domain["Data domain"]
    aqie_alert_back_end_service["alert-back-end-service"]
    aqie_back_end["back-end"]
    aqie_dc_backend["dc-backend"]
    aqie_docanalysispoc_backend["docanalysispoc-backend"]
    aqie_forecast_api["forecast-api"]
    aqie_historicaldata_backend["historicaldata-backend"]
    aqie_location_backend["location-backend"]
    aqie_monitoringstation_backend["monitoringstation-backend"]
    aqie_notify_service["notify-service"]
    aqie_prtr_backend["prtr-backend"]
  end
  subgraph Shared["Shared"]
    defra_forms["defra-forms"]
  end
  subgraph externals["External and platform systems"]
    azure_entra[["Microsoft Entra ID"]]
    cdp_uploader[["CDP Uploader"]]
    defra_sos[["DEFRA Sensor Observation Service (SOS)"]]
    google_tag_manager[["Google Tag Manager / Google Analytics"]]
    govuk_notify[["GOV.UK Notify"]]
    laqm_portal[["LAQM Portal API"]]
    met_office_sftp[["Met Office forecast SFTP"]]
    model_providers[["Azure OpenAI and AWS Bedrock"]]
    openfreemap[["OpenFreeMap"]]
    os_names[["Ordnance Survey Names API"]]
    os_places_ni[["Ordnance Survey Places (Northern Ireland)"]]
    postcodes_io[["postcodes.io"]]
    qualtrics[["Qualtrics"]]
    ricardo_ukair[["Ricardo UK-AIR API"]]
    ukair_atom[["DEFRA UK-AIR INSPIRE Atom download service"]]
    ukair_website[["DEFRA UK-AIR public website"]]
  end
    aqie_front_end -->|"GET /measurements<br/>GET /monitoringStationInfo"| aqie_back_end
    aqie_front_end -->|"GET /forecast"| aqie_forecast_api
    aqie_front_end -->|"GET /search/names/v1/find"| os_names
    aqie_front_end -->|"GET /ajax/forecast_text_summary.php"| ukair_website
    aqie_front_end -.->|"HTTPS"| qualtrics
    aqie_back_end ==>|"POST /api/login_check<br/>GET /api/pollutant_measurement_datas<br/>GET /api/pollutant_metadatas<br/>GET /api/site_meta_datas"| ricardo_ukair
    aqie_back_end -->|"GET /postcodes"| postcodes_io
    aqie_back_end ==>|"SFTP"| met_office_sftp
    aqie_back_end -->|"HTTPS/REST"| govuk_notify
    aqie_forecast_api ==>|"SFTP"| met_office_sftp
    aqie_location_backend -->|"GET /search/names/v1/find"| os_names
    aqie_monitoringstation_backend -->|"GET /monitoringStationInfo?with-closed=true&with-pollutants=1&stream=data"| aqie_back_end
    aqie_monitoringstation_backend -->|"POST /osnameplaces"| aqie_location_backend
    aqie_dataselector_frontend -->|"POST /AtomDataSelection<br/>POST /AtomDataSelectionJobStatus<br/>GET /AtomDataSelectionPollutantMaster<br/>POST /AtomDataSelectionPollutantDataSource<br/>+4 more"| aqie_historicaldata_backend
    aqie_dataselector_frontend -->|"POST /osnameplaces"| aqie_location_backend
    aqie_dataselector_frontend -->|"POST /monitoringstation"| aqie_monitoringstation_backend
    aqie_alert_back_end_service ==>|"POST /api/login_check<br/>GET /api/daqi_alerts<br/>GET /api/aqsr_alerts<br/>GET /api/site_meta_datas"| ricardo_ukair
    aqie_alert_back_end_service -.->|"GET /notify/unsubscribe-email-link"| aqie_front_end
    aqie_notify_service -->|"DELETE /opt-out-sms-alert"| aqie_alert_back_end_service
    aqie_notify_service -->|"HTTPS/REST"| govuk_notify
    aqie_dc_frontend -->|"GET /get-all/{type}<br/>GET /get/{type}/{id}"| aqie_dc_backend
    defra_forms -.->|"AWS SQS"| aqie_dc_backend
    aqie_dc_admin_frontend -->|"GET /applications/search<br/>PATCH /appliances/{id}/technical-review<br/>POST /admin/import/initiate"| aqie_dc_backend
    aqie_dc_admin_frontend -->|"HTTPS/OIDC"| azure_entra
    aqie_dc_backend -.->|"POST /upload-and-scan/{uploadId}<br/>POST /upload-callback"| cdp_uploader
    aqie_prtr_frontend -->|"GET /facilities/search<br/>GET /facilities/nearby<br/>GET /facilities/{id}/details<br/>GET /facilities/{id}/competent-authority<br/>+5 more"| aqie_prtr_backend
    aqie_prtr_backend -->|"POST /osnameplaces"| aqie_location_backend
    aqie_maps_frontend -->|"GET /monitoringStations<br/>GET /monitoringStationInfo<br/>GET /aurnData<br/>GET /forecasts"| aqie_back_end
    aqie_maps_frontend -->|"GET /forecast"| aqie_forecast_api
    aqie_demo_data_visualisations -->|"GET /measurements"| aqie_back_end
    aqie_docanalysisawspoc_frontend -->|"HTTPS/REST"| aqie_docanalysispoc_backend
    aqie_docanalysispoc_frontend -->|"HTTPS/REST"| aqie_docanalysispoc_backend
    aqie_docanalysispoc_backend -->|"HTTPS/REST"| model_providers
    aqie_front_end -->|"POST /setup-alert<br/>DELETE /opt-out-email-alert<br/>GET /aqsr-alert<br/>GET /daqi-alert"| aqie_alert_back_end_service
    aqie_front_end -->|"POST /subscribe/generate-otp<br/>POST /subscribe/validate-otp<br/>POST /subscribe/generate-link<br/>GET /subscribe/validate-link/{uuid}"| aqie_notify_service
    aqie_alert_back_end_service -->|"POST /send-notification"| aqie_notify_service
    aqie_alert_back_end_service ==>|"GET /forecast"| aqie_forecast_api
    aqie_notify_service -.->|"GET /notify/register/email-confirm-link"| aqie_front_end
    aqie_front_end -->|"POST /{tenant}/oauth2/v2.0/token"| azure_entra
    aqie_front_end -->|"HTTPS/REST"| os_places_ni
    aqie_front_end -->|"GET /postcodes"| postcodes_io
    aqie_front_end -->|"HTTPS"| google_tag_manager
    aqie_maps_prototype -->|"GET /monitoringStations<br/>GET /monitoringStationInfo<br/>GET /health"| aqie_back_end
    aqie_maps_prototype -->|"GET /forecast"| aqie_forecast_api
    aqie_maps_frontend -->|"HTTPS"| openfreemap
    aqie_maps_prototype -->|"HTTPS"| openfreemap
    aqie_demo_data_visualisations -->|"GET /service?service=AQD&version=1.0.0&request=GetObservation"| defra_sos
    aqie_demo_data_visualisations -->|"GET /postcodes/{postcode}<br/>GET /outcodes/{outcode}<br/>GET /places"| postcodes_io
    aqie_laqm_data_explorer -->|"GET /xapi/getLocalAuthorities/json<br/>GET /xapi/getRegions/json<br/>GET /xapi/getSingleLAData/{laId}/json<br/>GET /xapi/getSingleDTDataByYear/{year}/{laId}/{page}/{perPage}/json<br/>+2 more"| laqm_portal
    aqie_dataselector_frontend -->|"GET /xapi/getLocalAuthorities/json"| laqm_portal
    aqie_historicaldata_backend -->|"GET /data/atom-dls/observations/auto/GB_FixedObservations_{year}_{siteID}.xml<br/>GET /data/atom-dls/observations/non-auto/..."| ukair_atom
    aqie_historicaldata_backend -->|"POST /api/login_check<br/>GET /api/site_meta_datas?with-closed=true&with-pollutants=1"| ricardo_ukair
    aqie_historicaldata_backend -->|"GET /xapi/getLocalAuthorities/json<br/>GET /xapi/getSingleDTDataByYear/{year}/{laId}/{page}/{perPage}/json"| laqm_portal
    aqie_historicaldata_backend -.->|"POST /send-notification"| aqie_notify_service
    aqie_historicaldata_backend -->|"AWS SDK"| AWS_S3
    aqie_prtr_backend -->|"AWS SDK"| AWS_S3
    aqie_prtr_frontend -->|"HTTPS"| AWS_S3
    aqie_dc_backend -->|"AWS SDK"| AWS_S3
  classDef citizen fill:#d4e6f7,stroke:#1d70b8,color:#0b0c0c;
  classDef data fill:#d8eeda,stroke:#00703c,color:#0b0c0c;
  classDef shared fill:#fff3d4,stroke:#946b00,color:#0b0c0c;
  classDef ext fill:#eeeeee,stroke:#505a5f,color:#0b0c0c;
  class aqie_dataselector_frontend,aqie_dc_admin_frontend,aqie_dc_frontend,aqie_demo_data_visualisations,aqie_docanalysisawspoc_frontend,aqie_docanalysispoc_frontend,aqie_front_end,aqie_laqm_data_explorer,aqie_maps_frontend,aqie_maps_prototype,aqie_prtr_frontend citizen;
  class aqie_alert_back_end_service,aqie_back_end,aqie_dc_backend,aqie_docanalysispoc_backend,aqie_forecast_api,aqie_historicaldata_backend,aqie_location_backend,aqie_monitoringstation_backend,aqie_notify_service,aqie_prtr_backend data;
  class defra_forms shared;
  class azure_entra,cdp_uploader,defra_sos,google_tag_manager,govuk_notify,laqm_portal,met_office_sftp,model_providers,openfreemap,os_names,os_places_ni,postcodes_io,qualtrics,ricardo_ukair,ukair_atom,ukair_website ext;
```
