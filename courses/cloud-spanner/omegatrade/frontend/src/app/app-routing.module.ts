import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { AuthGuardService } from './services/auth-guard.service';
import { LoginComponent } from './components/login/login.component';
import { RegisterComponent } from './components/register/register.component';
import { ManageCompanyComponent } from './components/company/manage-company/manage-company.component';
import { SimulationComponent } from './components/simulation/simulation.component';
import {  StockDashboardComponent } from './components/stock-dashboard/stock-dashboard.component';

const routes: Routes = [
  { path: '', component: LoginComponent },
  { path: 'dashboard', component: StockDashboardComponent,canActivate: [AuthGuardService] },
  { path: 'sign-up', component: RegisterComponent },
  { path: 'simulations', component: SimulationComponent,canActivate: [AuthGuardService] },
  { path: 'companies', component: ManageCompanyComponent,canActivate: [AuthGuardService] },
];

@NgModule({
  imports: [RouterModule.forRoot(routes, { useHash: true })],
  exports: [RouterModule]
})
export class AppRoutingModule { }
