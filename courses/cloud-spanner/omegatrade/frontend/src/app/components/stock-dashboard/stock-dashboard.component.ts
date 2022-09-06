import { Component, OnInit, OnDestroy ,ViewChild } from '@angular/core';
import { Router,ActivatedRoute } from '@angular/router';
import { RestService } from '../../services/rest.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { take } from 'rxjs/operators';
import { SnackBarService } from '../../services/snackbar.service';
import { GoogleChartComponent } from 'angular-google-charts';
@Component({
  selector: 'app-stock-dashboard',
  templateUrl: './stock-dashboard.component.html',
  styleUrls: ['./stock-dashboard.component.css']
})
export class StockDashboardComponent implements OnInit, OnDestroy {

  selectedCompany: string = "";
  companyName: string = "";
  lastUpdatedTime;
  companies: any;
  loader: boolean=false;
  timerIds = [];
  areaChartData:any;
  showNodata:boolean=false;
  @ViewChild(GoogleChartComponent)
  public readonly chart: GoogleChartComponent;
  constructor(private snackBarService: SnackBarService, private route: ActivatedRoute,private router: Router, private _snackBar: MatSnackBar, private restService: RestService) {
  }

  /**
   *  Function to Initiate component.
   *  Initiating company lists
   */
  ngOnInit(): void {
    this.selectedCompany = this.route.snapshot.queryParamMap.get('companyId');
    this.getCompanies();
  }

  /**
   *  Function to get all companies.
   *  @returns  {null}
   */
  getCompanies() {
    this.restService.getData('companies/list')
      .pipe(take(1))
      .subscribe(
        response => {
          if (response && response.success) {
            this.companies = response.data;
            if (this.companies && this.companies.length > 0) {
              if (!this.selectedCompany || this.selectedCompany === "")
                this.selectedCompany = this.companies[0].companyId;
              this.getStockData();
            }
          }
        },
        error => {
          if (error && error.error && error.error.message) {
            this.snackBarService.openSnackBar(error.error.message, '');
          }
          this.clearAllTimeOuts();
          this.loader = false;
        });
  }

  /**
   *  Function to get all stockDatas for selected company.
   * 
   *  @returns  {null}
   */
  getStockData() {
    if (this.selectedCompany) {
      // clearing the chart to avoid showing previously loaded chart.
      if(this.chart && this.chart.chartWrapper){
        this.chart.chartWrapper.getChart().clearChart();
      }
      this.loader = true;
      this.restService.getData(`companies/dashboard/${this.selectedCompany}`)
        .pipe(take(1))
        .subscribe(
          response => {
            if (response && response.success) {
              const stocks = response.data.stocks;
              const company = response.data.company;
              if (stocks && stocks.length > 0) {
                this.parseStockDatas(stocks, company);
                this.showNodata = false;
              } else if (company && company.status === 'PROCESSING') {
                this.showNodata = false;
                this.companyName = company && company.companyName ? company.companyName : "";
                /**
                 * Retrying getStockData in the case of empty stocks at that current time. 
                 * But it may have data since the staus is in PROCESSING,
                 * so fetching the datas of running simulation in certain interval.
                 * 
                 */
                const id = setTimeout(() => {
                  this.getStockData();
                }, 5000);
                this.timerIds.push(id);
              }else{
                const company = this.companies.filter(company => company.companyId === this.selectedCompany)
                this.companyName = company[0].companyName;
                this.showNodata = true;
              }
              this.loader = false;
            }
          },
          error => {
            if (error && error.error && error.error.message) {
              this.snackBarService.openSnackBar(error.error.message, '');
            }
            this.clearAllTimeOuts();
            this.loader = false;
          });
    }
  }
  /**
   * Function to parse the stocks and form as per the chart data format.
   * updates the lastUpatedTime and redraws the chart.
   * 
   * @param stocks  contains unformatted stocks data
   * @param company contains company information - companyName,shortCode and status
   */
  parseStockDatas(stocks, company) {
    const chartData = [];
    this.lastUpdatedTime = stocks[(stocks.length - 1)].date;
    for (var i = 0; i < stocks.length; i++) {
      chartData.push([new Date(stocks[i].date), parseInt(stocks[i].currentValue)]);
    }
    this.createChart(chartData, company)
  }

  /**
   * Function to draw new chart for a company
   * @param chartData Formatted chart data
   * @param company contains company information.
   */
  createChart(chartData, company) {
    this.areaChartData = {
      type: 'AreaChart',
      data: chartData,
      columnNames: ["Date", company.companyName],
      options: {
        animation: {
          duration: 500,
          easing: 'out'
        },
        legend: {
          position: 'left'
        },
        title: company.companyName + ' Stock Price',
        chartArea:{width:"85%",height:"75%"},
        hAxis: {
          title: 'Date',
          direction: 1,
          slantedText: true,
          slantedTextAngle: 45,
        },
        vAxis: {
          title: 'Stock Price'
        },
      },
      height: 600
    };
    if (company && company.status === 'PROCESSING') {
      this.updateDashboard();
    }
  }

  updateDashboard() {
    if (this.selectedCompany && this.lastUpdatedTime) {
      this.restService.getData(`companies/dashboard/${this.selectedCompany}?date=${this.lastUpdatedTime}`)
        .pipe(take(1))
        .subscribe(
          response => {
            if (response && response.success) {
              const data = response.data.stocks;
              const company = response.data.company;
              if (company && company.status && company.status == 'COMPLETED') {
                // Canceling subscription when simulation completed
                this.clearAllTimeOuts()
              } else {
                if (data && data.length > 0) {
                  // updating lastUpdatedtime with current stock data
                  this.lastUpdatedTime = data[(data.length - 1)].date;
                  for (var i = 0; i < data.length; i++) {
                    this.areaChartData.data.push([new Date(data[i].date), parseInt(data[i].currentValue)]);
                    this.areaChartData.data = Object.assign([], this.areaChartData.data);
                  }
                }
                if (company && company.status == 'PROCESSING') {
                  /**
                   * Retrying getStockData in the case of empty stocks at that current time. 
                   * But it may have data since the staus is in PROCESSING,
                   * so fetching the datas of running simulation in certain interval.
                   * 
                   */
                  const id = setTimeout(() => {
                    this.updateDashboard();
                  }, 5000);
                  this.timerIds.push(id);
                }
              }
            }
          },
          error => {
            if (error && error.error && error.error.message) {
              this.snackBarService.openSnackBar(error.error.message, '');
            }
            this.clearAllTimeOuts();
            this.loader = false;
          });
    }
  }

  /**
   * Function to clear all timeout functions
   */
  clearAllTimeOuts() {
    if (this.timerIds && this.timerIds.length > 0) {
      const ids = this.timerIds;
      for (var i = 0; i < ids.length; i++) {
        clearTimeout(ids[i]);
      }
    }
  }

  ngOnDestroy() {
    this.clearAllTimeOuts();
  }

  /**
   * Function to clear the chart on Error.
   * @param chart 
   */
   onError(chart){
    if(chart)
      chart.clearChart();
    return;  
  }
}






