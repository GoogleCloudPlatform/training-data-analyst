import { Injectable } from '@angular/core';
import { catchError } from 'rxjs/operators';
import { Observable, throwError } from 'rxjs';
import { environment } from 'src/environments/environment';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { TokenStorageService } from './token-storage.service';

@Injectable({
    providedIn: 'root'
})

export class RestService {
    BASE_URL: string = environment.baseUrl;
    httpHeaders = new HttpHeaders().set('Content-Type', 'application/json');

    constructor(private tokenStorage: TokenStorageService, private httpClient: HttpClient) {
    }

    /**
     * Invoke a API call with POST method.
     *
     * @param path contains end point function of the API
     * @param payload contains request payload and query params.
     *
     * @return Array
     */
    postData(path, payload): Observable<any> {
        return this.httpClient.post(`${this.BASE_URL + path}`, payload).pipe(catchError(this.handleError));
    }

    /**
     * Invoke a API call with GET method.
     *
     * @param path contains end point and queryParams of the API
     *
     * @return Array
     */
    getData(path): Observable<any> {
        return this.httpClient.get(`${this.BASE_URL + path}`, ).pipe(catchError(this.handleError));
    }

    /**
     * Invoke a API call with PUT method.
     *
     * @param path contains end point function of the API
     * @param payload contains request payload and query params.
     *
     * @return Array
     */
    putData(path, payload): Observable<any> {
        return this.httpClient.put(`${this.BASE_URL + path}`, payload, )
            .pipe(catchError(this.handleError));
    }

    /**
     * Invoke a API call with DELETE method.
     *
     * @param path contains end point function and queryParams of the API
     * @return Array
     */
    deleteData(path): Observable<any> {
        return this.httpClient.delete(`${this.BASE_URL + path}`, )
            .pipe(catchError(this.handleError));
    }

    /**
     * Function to handle the error and return .
     *
     * @return Array
     */
    handleError(error: HttpErrorResponse): any {
        if (error.status === 401 && error.statusText === 'Unauthorized') {
            window.sessionStorage.removeItem('userInfo');
            window.sessionStorage.removeItem('authToken');
        }
        return throwError(error);
    }
}
